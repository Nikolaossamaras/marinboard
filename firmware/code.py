import board
import digitalio
import usb_hid
import time
import busio
import displayio
import terminalio
import wifi
import socketpool
import ssl
import os
import rtc
import adafruit_requests
import adafruit_ntp
import adafruit_displayio_ssd1306

from adafruit_display_text import label
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

#Configuration

WIFI_SSID = "YourSSID"
WIFI_PASSWORD = "YourPassword"
WIFI_TIMEOUT = 8  

UTC_OFFSET = 3

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") # change this in your .env file
OPENWEATHER_CITY = "Athens,GR" # change this to your city
WEATHER_REFRESH_TIME = 900 

NTP_REFRESH_RATE = 3600

ANIMATION_FRAME_DIR= "/marin"
ANIMATION_FRAME_COUNT = 56
ANIMATION_FRAME_INTERVAL = 0.15

OLED_WIDTH = 128
OLED_HEIGHT = 32
OLED_I2C_ADDRESS = 0x3C
SDA_PIN = board.GP26
SCL_PIN = board.GP27

COL_PINS =[
    board.GP0,
    board.GP1,
    board.GP2,
    board.GP3,
    board.GP4,
    board.GP5,
    board.GP6,
    board.GP7,
    board.GP8,
    board.GP9,
    board.GP10,
    board.GP11,
    board.GP12,
    board.GP13,
    board.GP14,
    board.GP15
]#columns 1-16

ROW_PINS = [
    board.GP17,
    board.GP18,
    board.GP19,
    board.GP20,
    board.GP21,
    board.GP22
]#rows 1-6

columns =[]

for pin in COL_PINS:
    col = digitalio.DigitalInOut(pin)
    col.direction = digitalio.Direction.OUTPUT
    col.value = False
    columns.append(col)
rows = []

for pin in ROW_PINS:
    row = digitalio.DigitalInOut(pin)
    row.direction = digitalio.Direction.INPUT
    row.pull = digitalio.Pull.DOWN
    rows.append(row)


displayio.release_displays()
i2c= busio.I2C(SCL_PIN,SDA_PIN)
display_bus = displayio.I2CDisplay(i2c, device_address=OLED_I2C_ADDRESS)
display = adafruit_displayio_ssd1306.SSD1306(display_bus,width=OLED_WIDTH,height=OLED_HEIGHT)


# PAGE 1


_reported_missing = set()
animation_group = displayio.Group()
_current_frame_bitmap = None
_current_frame_tilegrid = None

def load_animation_frame(index):
    global _current_frame_bitmap, _current_frame_tilegrid

    path = "{}/frame{:03d}.bmp".format(ANIMATION_FRAME_DIR, index + 1)
    try:
        bitmap = displayio.OnDiskBitmap(path)
    except OSError:
        if path not in _reported_missing:
            print("Failed to load frame:",path)
            _reported_missing.add(path)
        return

    tilegrid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)

    if _current_frame_tilegrid is not None:
        animation_group.remove(_current_frame_tilegrid)

    animation_group.append(tilegrid)
    _current_frame_bitmap = bitmap
    _current_frame_tilegrid = tilegrid

# Page 2
clock_group = displayio.Group()
clock_time_label = label.Label(terminalio.FONT, text="--:--:--",x=25,y=8,scale =1)
clock_group.append(clock_time_label)
clock_date_label = label.Label(terminalio.FONT, text="--/--/----",x=25,y=20,scale =1)
clock_group.append(clock_date_label)

# Page 3
weather_group = displayio.Group()
weather_temp_label = label.Label(terminalio.FONT, text="--°C",x=5,y=8,scale =1)
weather_group.append(weather_temp_label)
weather_cond_label = label.Label(terminalio.FONT,text="---",x=60,y=8,scale =1)
weather_group.append(weather_cond_label)
weather_hum_label = label.Label(terminalio.FONT,text="--%",x=5,y=22,scale =1)
weather_group.append(weather_hum_label)

PAGES =[animation_group, clock_group, weather_group]
current_page_index = 0
display.root_group = PAGES[current_page_index]

# WIFI

wifi_connected = False
requests_session = None
ntp = None

try:
    wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD, timeout=WIFI_TIMEOUT)
    wifi_connected = True
except (ConnectionError, OSError):
    wifi_connected = False

if wifi_connected:
    pool = socketpool.SocketPool(wifi.radio)
    requests_session = adafruit_requests.Session(pool, ssl.create_default_context())
    ntp = adafruit_ntp.NTP(pool, tz_offset=UTC_OFFSET)

# States

now=time.monotonic()

last_animation_tick = now
animation_frame_index = 0

last_clock_update = 0
last_ntp_sync = 0
time_synced = False

last_weather_fetch = 0
weather_ok = False

WEEKDAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def sync_ntp_time():
    global time_synced
    if not  wifi_connected or ntp is None:
        return
    try:
        rtc.RTC().datetime = ntp.datetime
        time_synced = True
    except(ValueError,OSError):
        time_synced = False

def fetch_weather():
    global weather_ok
    if not wifi_connected or requests_session is None:
        weather_ok = False
        return None
    url=(
        "https://api.openweathermap.org/data/2.5/weather"
        "?q={city}&appid={key}&units=metric"
    ).format(city=OPENWEATHER_CITY,key=OPENWEATHER_API_KEY)
    try:
        response = requests_session.get(url,timeout=5)
        data = response.json()
        response.close()
        weather_ok = True
        return{
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["main"]
        }
    except (OSError,ValueError,KeyError):
        weather_ok = False
        return None

def update_clock_display():
    t = time.localtime()
    time_str = "{:02d}:{:02d}:{:02d}".format(t.tm_hour,t.tm_min,t.tm_sec)
    date_str = "{:02d}/{:02d}/{:04d}".format(t.tm_mday,t.tm_mon,t.tm_year)

    if clock_time_label.text != time_str:
        clock_time_label.text = time_str
    if clock_date_label.text != date_str:
        clock_date_label.text = date_str

def update_weather_display(weather):
    if weather is None:
        weather_cond_label.text = "Offline"
        return
    weather_temp_label.text = "{:.1f}C".format(weather["temp"])
    weather_cond_label.text = weather["condition"]
    weather_hum_label.text = "Hum: {}%".format(weather["humidity"])

def switch_page():
    global current_page_index
    current_page_index = (current_page_index + 1) % len(PAGES)
    display.root_group = PAGES[current_page_index]



# Keyboard mapping
KEYMAP = {
    (0,0):Keycode.ESCAPE,
    (0,1):Keycode.F1,
    (0,2):Keycode.F2,
    (0,3):Keycode.F3,
    (0,4):Keycode.F4,
    (0,5):Keycode.F5,
    (0,6):Keycode.F6,
    (0,7):Keycode.F7,
    (0,8):Keycode.F8,
    (0,9):Keycode.F9,
    (0,10):Keycode.F10,
    (0,11):Keycode.F11,
    (0,12):Keycode.F12,
    (0,13):Keycode.PRINT_SCREEN,
    (0,14):Keycode.SCROLL_LOCK,
    (0,15):Keycode.DELETE,
    (1,0):Keycode.GRAVE_ACCENT,
    (1,1):Keycode.ONE,
    (1,2):Keycode.TWO,
    (1,3):Keycode.THREE,
    (1,4):Keycode.FOUR,
    (1,5):Keycode.FIVE,
    (1,6):Keycode.SIX,
    (1,7):Keycode.SEVEN,
    (1,8):Keycode.EIGHT,
    (1,9):Keycode.NINE,
    (1,10):Keycode.ZERO,
    (1,11):Keycode.MINUS,
    (1,12):Keycode.EQUALS,
    (1,14):Keycode.BACKSPACE,
    (1,15):Keycode.HOME,
    (2,0):Keycode.TAB,
    (2,1):Keycode.Q,
    (2,2):Keycode.W,
    (2,3):Keycode.E,
    (2,4):Keycode.R,
    (2,5):Keycode.T,
    (2,6):Keycode.Y,
    (2,7):Keycode.U,
    (2,8):Keycode.I,
    (2,9):Keycode.O,
    (2,10):Keycode.P,
    (2,11):Keycode.LEFT_BRACKET,
    (2,12):Keycode.RIGHT_BRACKET,
    (2,14):Keycode.BACKSLASH,
    (2,15):Keycode.PAGE_UP,
    (3,0):Keycode.CAPS_LOCK,
    (3,2):Keycode.A,
    (3,3):Keycode.S,
    (3,4):Keycode.D,
    (3,5):Keycode.F,
    (3,6):Keycode.G,
    (3,7):Keycode.H,
    (3,8):Keycode.J,
    (3,9):Keycode.K,
    (3,10):Keycode.L,
    (3,11):Keycode.SEMICOLON,
    (3,12):Keycode.QUOTE,
    (3,14):Keycode.ENTER,
    (3,15):Keycode.PAGE_DOWN,
    (4,0):Keycode.LEFT_SHIFT,
    (4,2):Keycode.Z,
    (4,3):Keycode.X,
    (4,4):Keycode.C,
    (4,5):Keycode.V,
    (4,6):Keycode.B,
    (4,7):Keycode.N,
    (4,8):Keycode.M,
    (4,9):Keycode.COMMA,
    (4,10):Keycode.PERIOD,
    (4,11):Keycode.FORWARD_SLASH,
    (4,13):Keycode.RIGHT_SHIFT,
    (4,14):Keycode.UP_ARROW,
    (4,15):Keycode.END,
    (5,0):Keycode.LEFT_CONTROL,
    (5,1):Keycode.LEFT_GUI,
    (5,11):"FN",
    (5,12):Keycode.RIGHT_CONTROL,
    (5,13):Keycode.LEFT_ARROW,
    (5,14):Keycode.DOWN_ARROW,
    (5,15):Keycode.RIGHT_ARROW
}

kbd = Keyboard(usb_hid.devices)
pressed_state = {}

def scan_matrix():
    for col_index, col in enumerate(columns):
        col.value = True
        for row_index, row in enumerate(rows):
            key = (row_index , col_index)
            is_pressed = row.value

            was_pressed = pressed_state.get(key,False)

            if key in KEYMAP:
                keycode = KEYMAP[key]

                if is_pressed and not was_pressed:
                    if keycode =="FN":
                        switch_page()
                    else:
                        kbd.press(keycode)

                elif not is_pressed and was_pressed:
                    if keycode !="FN":
                        kbd.release(keycode)

            pressed_state[key] = is_pressed

        col.value = False

# Main loop
while True:

    now = time.monotonic()

    scan_matrix()

    if current_page_index == 0 and (now-last_animation_tick) >= ANIMATION_FRAME_INTERVAL:
        load_animation_frame(animation_frame_index)
        animation_frame_index = (animation_frame_index + 1) % ANIMATION_FRAME_COUNT
        last_animation_tick = now

    if wifi_connected and (now - last_ntp_sync) >= NTP_REFRESH_RATE:
        sync_ntp_time()
        last_ntp_sync = now

    if current_page_index == 1 and (now - last_clock_update) >= 1:
        update_clock_display()
        last_clock_update = now

    if current_page_index == 2 and (now - last_weather_fetch) >= WEATHER_REFRESH_TIME:
        weather_data = fetch_weather()
        if current_page_index == 2:
            update_weather_display(weather_data)
        last_weather_fetch = now



