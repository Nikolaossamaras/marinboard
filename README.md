# MariBoard
>A costum keyboard featuring the anime Character Marin Kitagawa

## What is it
It's a costum keyboard with the thematic of Marin kitagawa from the anime My-dress-up-darling by cloverworks. It's layout is keycool kc84 75% . It includes 84 keys & an oled diplay and it's powered by in raspberry pi pico W , allowing it to connect to the internet in order to display information to the oled display like the Time , date & Weather

## Why i built it?

I really love anime and my favourite character is Marin Kitagawa. I also like electronics and making projects so i sat down and though which will be my next project and i decided on this one a CUSTOM KEYBOARD that is designed with diffrent Marin Kitagawa and dress-up-darling pictures.

## PCB Preview


## Schematic


## CAD

## Requirements

| Product | quantity |
| --- | --- |
| OLED Module 128x32 0.91" i2c | 1pc |
| Raspberry Pi Pico W | 1pc |
| 1N4148W diodes | 84pc |
| costum pcb | 1 |
| 3D printed case | 1 |


## How to assemble it?

### 1st step
your first step is cloning this repo to your Pc so you have all the required files

### 2nd step

Get your pcb , go to a pcb production company and upload the gerber.zip file on their site and order the board

### 3rd step

While you wait for your pcb you can start 3d printing your case which is in Cad folder, there you will see 2 files both are the same one but diffrent format.

> if you don't have a 3d printer you can 3d print it from the same company from which you ordered your pcb

### 4th step 

Now that you have the pcb you will need to solder everything together
if you get an assembled board you wont need to solder the diodes as the are already will come installed , but if you didn't 
your next step is to solder the diodes together on the board like instructed in the schematic

### 5th step
when you finish with the diodes check them with a multimeter to check if they are connected the correct way

### 6th step
now solder the microcontroller and the push button

### 7th step 
solder the oled display in place

### 8th step 
add the switches to the top pcb in order and then put it on top of the middle pcb(main pcb), be careful to align every switch correctly in order the soldering of them to procced smoothly

### 9th step 
add nuts to the 3d printed case at the button 
then place on top of it the pcb's in order (first the bottom , then the main and then the top one) after that pass a screw in each corner mounting hole of the pcb until it's reached the nut , be careful not to damage the main board

### 10th step 
You will need to download the latest .uf2 stable file on Circuitpython for pico W (make sure it's the W not the normal version)

### 11th step
hold the bootsel button on the board while inserting the board to your pc release the button when it's connected **do this step before soldering the top and main pcb together**

### 12th step 

copy the .uf2 file to the microcontroller

the board will reboot and then a drove called ```Circuitpython``` should appear 

### 13th step
Your main program must be named code.py (or main.py) and placed at the root of CIRCUITPY
For libraries , grab the matching version of the CircuitPython Library Bundle and copy the needed .mpy files into a /lib folder on CIRCUITPY

### 14th step
when you upload the code to the drive it should become an input meaning the drive will disapear

## Licence

This project is under the MIT licence 
