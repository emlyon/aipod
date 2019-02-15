# https://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi?view=all
# https://www.pygame.org/docs/ref/mixer.html

import json
import time
from random import randrange
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import pygame

# Load data
with open('data.json') as json_file:
    data = json.load(json_file)

nbArticles = len(data)

# Init LCD
lcd_columns = 16
lcd_rows = 2
lcd_rs = digitalio.DigitalInOut(board.D22)
lcd_en = digitalio.DigitalInOut(board.D17)
lcd_d4 = digitalio.DigitalInOut(board.D25)
lcd_d5 = digitalio.DigitalInOut(board.D24)
lcd_d6 = digitalio.DigitalInOut(board.D23)
lcd_d7 = digitalio.DigitalInOut(board.D18)

lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)

lcd.clear()

# Init button
button = digitalio.DigitalInOut(board.D4)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP
button.previous_state = 'UP'
do_release = False

# Init mp3 player
pygame.init()
music = pygame.mixer.music

tick_delay = 0.3
tick = start_time = time.time()

lcd_line_1 = ' ' * 16
lcd_line_2 = ' ' * 16

def map_value(value, istart, istop, ostart, ostop):
    return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))

do_fade_in = False
def fade_in(start_time, duration):
    global music, time, do_fade_in
    v = music.get_volume()
    if v < 1:
        music.set_volume(map_value(time.time(), start_time, start_time + duration, 0, 1))
    else:
        do_fade_in = False

do_fade_out = False
def fade_out(start_time, duration):
    global time, music, lcd, do_fade_out
    v = music.get_volume()
    if v > 0:
        music.set_volume(map_value(time.time(), start_time, start_time + duration, 1, 0))
    else:
        music.stop()
        lcd.message = (' ' * 16) + "\n" + (' ' * 16)
        do_fade_out = False

def play_song():
    global data, lcd_line_1, lcd_line_2, music, do_fade_in, start_fade_time

    n = randrange(nbArticles)

    prefix = ' ' * 16
    lcd_line_1 = prefix + data[n]['line1']
    lcd_line_2 = prefix + data[n]['line2']
    lcd_line_1_len = len(lcd_line_1)
    lcd_line_2_len = len(lcd_line_2)

    # make both line the same length
    if lcd_line_1_len < lcd_line_2_len:
        lcd_line_1 = lcd_line_1 + ' ' * (lcd_line_2_len - lcd_line_1_len)
    else:
        lcd_line_2 = lcd_line_2 + ' ' * (lcd_line_1_len - lcd_line_2_len)

    music.set_volume(0)
    music.load('mp3s/' + data[n]['mp3'])
    music.play()

    do_fade_in = True
    start_fade_time = time.time()

# Start main loop
while True:
    now = time.time()
    elapsed_time = now - start_time

    button.is_pressed = not button.value

    if button.is_pressed:
        do_release = False

        if button.previous_state == 'UP': # on button press
            button.previous_state = 'DOWN'
            play_song()

    else:
        if button.previous_state == 'DOWN': # on button release
            do_release = True
            start_release_time = now

    if do_release:
        if now - start_release_time > 4 and not button.is_pressed:
            button.previous_state = 'UP'

            if music.get_busy():
                do_fade_out = True
                start_fade_time = now

    if music.get_busy():
        if do_fade_out:
            fade_in(start_fade_time, 5)
        elif do_fade_in:
            fade_out(start_fade_time, 5)
        
        # update lcd message
        index = int(elapsed_time / tick_delay) % len(lcd_line_1)
        line_1 = (lcd_line_1 * 2)[index:min(index + 16, len(lcd_line_1 * 2))]
        line_2 = (lcd_line_2 * 2)[index:min(index + 16, len(lcd_line_2 * 2))]
        lcd.message = line_1 + '\n' + line_2 

    elif button.is_pressed:
        # play a new song
        play_song()

    time.sleep(0.01) # small delay
