import random
import board
import audiocore
import audiobusio
from adafruit_debouncer import Button
from digitalio import DigitalInOut, Direction, Pull
import neopixel
import adafruit_lis3dh
from adafruit_ticks import ticks_ms, ticks_add, ticks_less
import colorsys
import time

HIT_THRESHOLD = 120
SWING_THRESHOLD = 130
RED = (255, 0, 0)
YELLOW = (125, 255, 0)
GREEN = (0, 255, 0)
CYAN = (0, 125, 255)
BLUE = (0, 0, 255)
PURPLE = (125, 0, 255)
WHITE = (255, 255, 255)
COLORS = [RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE]
BLACK = (0,0,0)

# enable external power pin
# provides power to the external components
external_power = DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = Direction.OUTPUT

audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)

# external neopixels
NUM_PIXELS = 50
pixels = neopixel.NeoPixel(
    board.EXTERNAL_NEOPIXELS, NUM_PIXELS, auto_write=False, pixel_order="GRB"
)
pixels.brightness = 0.1

# onboard LIS3DH
i2c = board.I2C()
int1 = DigitalInOut(board.ACCELEROMETER_INTERRUPT)
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)
# Accelerometer Range (can be 2_G, 4_G, 8_G, 16_G)
lis3dh.range = adafruit_lis3dh.RANGE_2_G
lis3dh.set_tap(1, HIT_THRESHOLD)

# button 1
b1pin = DigitalInOut(board.D5)
b1pin.direction = Direction.INPUT
b1pin.pull = Pull.UP
button1 = Button(b1pin, long_duration_ms=1000)

# button 2
b2pin = DigitalInOut(board.D6)
b2pin.direction = Direction.INPUT
b2pin.pull = Pull.UP
button2 = Button(b2pin, long_duration_ms=1000)

# button 3
b3pin = DigitalInOut(board.D9)
b3pin.direction = Direction.INPUT
b3pin.pull = Pull.UP
button3 = Button(b3pin, long_duration_ms=1000)

def play_sound(fname, loop=False):
    try:
        wave_file = open("sounds/" + fname, "rb")
        wave = audiocore.WaveFile(wave_file)
        audio.stop()
        audio.play(wave, loop=loop)
    except Exception as e:  # noqa: E722
        print(e)
        return

def main():
    main_color = RED

    external_power.value = 1
    print("play")
    play_sound("zz_march.wav")
    print("play done")
    while True:
        pixels.fill(BLACK)
        for k in range(10):
            i = random.randint(0, NUM_PIXELS-1)
            x = random.randint(0, 10)
            if x <= 1:
                c = random.randint(0, len(COLORS)-1)
                pixels[i] = COLORS[c]
            else:
                pixels[i] = main_color
        pixels.show()
        for i in range(10):
            button1.update()
            button2.update()
            button3.update()
            if button1.short_count == 1:
                print("button 1 pressed")
                main_color = RED
            if button2.short_count == 1:
                print("button 2 pressed")
                main_color = GREEN
            if button3.short_count == 1:
                print("button 3 pressed")
                main_color = BLUE
            time.sleep(0.01)



if __name__ == "__main__":
    main()
