import random
import board
import audiocore
import audiobusio
from adafruit_debouncer import Button
from digitalio import DigitalInOut, Direction, Pull
import neopixel
import adafruit_lis3dh
import time
import asyncio
from adafruit_ticks import ticks_ms, ticks_add, ticks_less
import audiomp3


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
BLACK = (0, 0, 0)
VIOLET = (200, 60, 150)

MAIN_COLORS = [VIOLET, RED, GREEN, BLUE]

SOUNDS = [
    "apfelmus-l",
    "eltern",
    "erdnussflips-j",
    "erdnussflips",
    "fahrrad-j",
    "geschwister",
    "ich-heisse-mara",
    "mara-j",
    "mara-l2",
    "mara-l",
]

COLOR_MODES = ["const", "blink"]

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
button_blue = Button(b1pin, long_duration_ms=1000)

# button 2
b2pin = DigitalInOut(board.D6)
b2pin.direction = Direction.INPUT
b2pin.pull = Pull.UP
button_black = Button(b2pin, long_duration_ms=1000)

# button 3
b3pin = DigitalInOut(board.D9)
b3pin.direction = Direction.INPUT
b3pin.pull = Pull.UP
button_white = Button(b3pin, long_duration_ms=1000)


class State:
    def __init__(self):
        self.main_color_idx = 0
        self.color_mode_idx = 0
        self.tick = ticks_ms()


state = State()


def play_sound(fname, loop=False, wait=False):
    wave_file = open("sounds/" + fname + ".wav", "rb")
    wave = audiocore.WaveFile(wave_file)
    fpath = "sounds/" + fname
    audio.stop()
    audio.play(wave)
    if wait:
        while audio.playing:
            time.sleep(0.1)

ANIM_SPEED = 100

async def light_and_sounds():
    while True:
        color_mode = COLOR_MODES[state.color_mode_idx]

        if not ticks_less(ticks_ms(), state.tick):
            if color_mode == "blink":
                pixels.fill(BLACK)
                for k in range(10):
                    i = random.randint(0, NUM_PIXELS - 1)
                    x = random.randint(0, 10)
                    if x <= 1:
                        c = random.randint(0, len(COLORS) - 1)
                        pixels[i] = COLORS[c]
                    else:
                        pixels[i] = MAIN_COLORS[state.main_color_idx]
                pixels.show()
                state.tick = ticks_add(ticks_ms(), ANIM_SPEED)
            elif color_mode == "const":
                c = MAIN_COLORS[state.main_color_idx]
                pixels.fill(c)
                pixels.show()
            else:
                pass
        await asyncio.sleep(0.01)


async def handle_events():
    print("handle events")
    while True:
        button_blue.update()
        button_black.update()
        button_white.update()

        if button_blue.short_count == 1:
            print("button blue pressed")
            state.main_color_idx = (state.main_color_idx + 1) % len(MAIN_COLORS)
        if button_black.short_count == 1:
            print("button black pressed")
            i = random.randint(0, len(SOUNDS) - 1)
            play_sound(SOUNDS[i])
        if button_white.short_count == 1:
            print("button white pressed")
            state.color_mode_idx = (state.color_mode_idx + 1) % len(COLOR_MODES)
        await asyncio.sleep(0.0)


async def main():
    external_power.value = 1

    main_tasks = [
        asyncio.create_task(light_and_sounds()),
        asyncio.create_task(handle_events()),
    ]

    await asyncio.gather(*main_tasks)


if __name__ == "__main__":
    asyncio.run(main())
