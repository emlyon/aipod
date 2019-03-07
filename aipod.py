import json
import time
from random import randrange
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import pygame

def init_lcd():
    global digitalio, board, characterlcd, time, lcd, lcd_columns, lcd_line_1, lcd_line_2, tick_delay, last_tick, start_time

    lcd_columns = 16
    lcd_rows = 2
    lcd_rs = digitalio.DigitalInOut(board.D16)
    lcd_en = digitalio.DigitalInOut(board.D12)
    lcd_d4 = digitalio.DigitalInOut(board.D25)
    lcd_d5 = digitalio.DigitalInOut(board.D24)
    lcd_d6 = digitalio.DigitalInOut(board.D23)
    lcd_d7 = digitalio.DigitalInOut(board.D18)
    lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)
    lcd.clear()
    lcd_line_1 = ' ' * 16
    lcd_line_2 = ' ' * 16
    tick_delay = 0.3
    last_tick = time.time()
    start_time = time.time()

def init_button():
    global digitalio, button, do_release
    button = digitalio.DigitalInOut(board.D4)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    button.previous_state = 'UP'
    do_release = False

def init_player():
    global pygame, music, do_fade_in, do_fade_out
    pygame.init()
    music = pygame.mixer.music
    do_fade_in = False
    do_fade_out = False

def init():
    init_lcd()
    init_button()
    init_player()

def print_git_status():
    global json, lcd, time
    with open('/home/pi/git_status.json') as git_file:
        git_status = json.load(git_file)['result']
    lcd.message = git_status
    time.sleep(5)
    lcd.clear()

def load_data():
    global data, nb_articles

    with open('output.json') as json_file:
        data = json.load(json_file)
        nb_articles = len(data)

def map_value(value, istart, istop, ostart, ostop):
    return ostart + (ostop - ostart) * ((value - istart) / (istop - istart)) if value < istop else ostop

def fade_in(start, duration):
    global music, time, do_fade_in
    v = map_value(time.time(), start, start + duration, 0, 100)/100
    music.set_volume(v)
    if v >= 1:
        do_fade_in = False

def fade_out(start, duration):
    global music, time, lcd, do_fade_out, lcd_line_1, lcd_line_2
    v = map_value(time.time(), start, start + duration, 100, 0)/100
    music.set_volume(v)
    if v <= 0:
        music.stop()
        lcd_line_1 = ' ' * 16
        lcd_line_2 = ' ' * 16
        do_fade_out = False

def play_song():
    print('play a new song')
    global nb_articles, data, lcd_line_1, lcd_line_2, music, do_fade_in, start_fade_time

    n = randrange(nb_articles)

    prefix = ' ' * 16
    lcd_line_1 = prefix + data[str(n)]['line1']
    lcd_line_2 = prefix + data[str(n)]['line2']
    lcd_line_1_len = len(lcd_line_1)
    lcd_line_2_len = len(lcd_line_2)

    # make both line the same length
    if lcd_line_1_len < lcd_line_2_len:
        lcd_line_1 = lcd_line_1 + ' ' * (lcd_line_2_len - lcd_line_1_len)
    else:
        lcd_line_2 = lcd_line_2 + ' ' * (lcd_line_1_len - lcd_line_2_len)

    music.set_volume(0)
    music.load('mp3s/' + data[str(n)]['filename'])
    music.play()

    do_fade_in = True
    start_fade_time = time.time()

init()
print_git_status()
load_data()

# Start main loop
print('Starting main loop')
while True:
    now = time.time()
    elapsed_time = now - start_time

    button.is_pressed = not button.value

    if button.is_pressed:
        do_release = False
        if button.previous_state == 'UP': # on button press
            print('button pressed')
            button.previous_state = 'DOWN'
            play_song()
            time.sleep(.5)
            start_time = time.time()
            elapsed_time = 0
    else:
        if button.previous_state == 'DOWN' and not do_release: # on button release
            print('button released')
            do_release = True
            start_release_time = now

    if do_release:
        # Check if button is still released after 4 seconds, fade out and stop music
        if now - start_release_time > 4 and not button.is_pressed:
            if button.previous_state == 'DOWN' and music.get_busy() == 1:
                print('starting fade out')
                do_fade_out = True
                start_fade_time = now
                button.previous_state = 'UP'

    if music.get_busy() == 1:
        if do_fade_out:
            fade_out(start_fade_time, 5)
        elif do_fade_in:
            fade_in(start_fade_time, 2)
    elif button.is_pressed:
        # play a new song
        button.previous_state == 'UP'

    # update lcd message
    if now - last_tick > tick_delay:
        index = int(elapsed_time / tick_delay) % len(lcd_line_1)
        line_1 = (lcd_line_1 * 2)[index:min(index + 16, len(lcd_line_1 * 2))]
        line_2 = (lcd_line_2 * 2)[index:min(index + 16, len(lcd_line_2 * 2))]
        # print(line_1 + '\n' + line_2)
        lcd.clear()
        lcd.message = line_1 + '\n' + line_2
        last_tick = time.time()

    time.sleep(0.05) # small delay
