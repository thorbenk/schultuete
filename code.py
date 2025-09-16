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

from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.solid import Solid
import adafruit_led_animation.color as anim_color

HIT_THRESHOLD = 120
SWING_THRESHOLD = 130

ANIM_COLORS = [
    anim_color.PURPLE,
    anim_color.RED,
    anim_color.GREEN,
    anim_color.BLUE,
    anim_color.CYAN,
    anim_color.YELLOW,
]
ANIM_COLOR_NAMES = [
    "PURPLE",
    "RED",
    "GREEN",
    "BLUE",
    "CYAN",
    "YELLOW",
]

VIOLET = (200, 60, 150)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

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

ANIMATION_MODES = [
    "pulse",
    "sparkle",
    "solid",
    "blink",
    "comet",
    "chase",
    "rainbow",
    "rainbow_chase",
    "rainbow_comet",
    "custom_sparkle"
]

BRIGHTNESSES = [0.1, 0.2, 0.3, 0.4]

# enable external power pin
external_power = DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = Direction.OUTPUT

audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)

# external neopixels
NUM_PIXELS = 50
pixels = neopixel.NeoPixel(
    board.EXTERNAL_NEOPIXELS, NUM_PIXELS, auto_write=False, pixel_order="GRB"
)

# onboard LIS3DH
i2c = board.I2C()
int1 = DigitalInOut(board.ACCELEROMETER_INTERRUPT)
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)
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


class NonBlockingAnimation:
    """Wrapper for LED animations to make them non-blocking"""
    def __init__(self, animation, update_interval_ms=50):
        self.animation = animation
        self.update_interval_ms = update_interval_ms
        self.last_update = ticks_ms()

    def update(self):
        """Non-blocking update - only animates if enough time has passed"""
        now = ticks_ms()
        if ticks_less(ticks_add(self.last_update, self.update_interval_ms), now):
            self.animation.animate()
            self.last_update = now


class CustomSparkle:
    """Custom non-blocking sparkle animation"""
    def __init__(self, pixels, color, num_sparkles=10, update_interval_ms=100):
        self.pixels = pixels
        self.color = color
        self.num_sparkles = num_sparkles
        self.update_interval_ms = update_interval_ms
        self.last_update = ticks_ms()
        self.active_sparkles = {}  # position: remaining_frames

    def update(self):
        now = ticks_ms()
        if ticks_less(ticks_add(self.last_update, self.update_interval_ms), now):
            self._animate()
            self.last_update = now

    def _animate(self):
        # Clear all pixels
        self.pixels.fill(BLACK)

        # Update existing sparkles
        expired = []
        for pos, frames in self.active_sparkles.items():
            if frames <= 0:
                expired.append(pos)
            else:
                self.pixels[pos] = self.color
                self.active_sparkles[pos] = frames - 1

        # Remove expired sparkles
        for pos in expired:
            del self.active_sparkles[pos]

        # Add new sparkles
        while len(self.active_sparkles) < self.num_sparkles:
            pos = random.randint(0, NUM_PIXELS - 1)
            if pos not in self.active_sparkles:
                self.active_sparkles[pos] = random.randint(3, 8)

        self.pixels.show()


class State:
    def __init__(self):
        self.main_color_idx = 0
        self.animation_mode_idx = 0
        self.brightness_idx = 0
        self.current_animation = None
        self.special_effect = None
        self.special_effect_end_time = 0
        self.setup_animations()

    def setup_animations(self):
        """Initialize all animation objects with non-blocking wrappers"""
        speed = 0.1
        current_color = ANIM_COLORS[self.main_color_idx % len(ANIM_COLORS)]

        # Create individual animations with non-blocking wrappers
        self.animations = {
            "solid": NonBlockingAnimation(
                Solid(pixels, color=current_color), 1000
            ),
            "blink": NonBlockingAnimation(
                Blink(pixels, speed=0.5, color=current_color), 50
            ),
            "pulse": NonBlockingAnimation(
                Pulse(pixels, speed=speed, color=current_color, period=3), 50
            ),
            "comet": NonBlockingAnimation(
                Comet(pixels, speed=speed, color=current_color, tail_length=10, bounce=True), 50
            ),
            "chase": NonBlockingAnimation(
                Chase(pixels, speed=speed, color=current_color, size=3, spacing=6), 50
            ),
            "rainbow": NonBlockingAnimation(
                Rainbow(pixels, speed=speed, period=2), 50
            ),
            "sparkle": NonBlockingAnimation(
                Sparkle(pixels, speed=speed, color=current_color, num_sparkles=10), 50
            ),
            "rainbow_chase": NonBlockingAnimation(
                RainbowChase(pixels, speed=speed, size=3, spacing=2, step=8), 50
            ),
            "rainbow_comet": NonBlockingAnimation(
                RainbowComet(pixels, speed=speed, tail_length=7, bounce=True), 50
            ),
            "custom_sparkle": CustomSparkle(pixels, current_color, num_sparkles=15, update_interval_ms=80)
        }

        # Set current animation
        mode_name = ANIMATION_MODES[self.animation_mode_idx]
        self.current_animation = self.animations[mode_name]

    def update_color(self):
        """Update the color for color-based animations"""
        current_color = ANIM_COLORS[self.main_color_idx % len(ANIM_COLORS)]

        # Update animations that use colors
        for name, wrapper in self.animations.items():
            if name == "custom_sparkle":
                wrapper.color = current_color
            elif hasattr(wrapper.animation, 'color') and name not in ["rainbow", "rainbow_chase", "rainbow_comet"]:
                wrapper.animation.color = current_color

        # Update current animation
        mode_name = ANIMATION_MODES[self.animation_mode_idx]
        self.current_animation = self.animations[mode_name]

        # make sure a redraw is triggered
        self.current_animation.last_update = 0

    def next_animation_mode(self):
        """Switch to next animation mode"""
        self.animation_mode_idx = (self.animation_mode_idx + 1) % len(ANIMATION_MODES)
        mode_name = ANIMATION_MODES[self.animation_mode_idx]
        self.current_animation = self.animations[mode_name]
        print(f"Switched to animation: {mode_name}")

    def next_color(self):
        """Switch to next color and update animations"""
        self.main_color_idx = (self.main_color_idx + 1) % len(ANIM_COLORS)
        self.update_color()
        color_name = ANIM_COLOR_NAMES[self.main_color_idx % len(color_names)]
        print(f"Switched to color: {color_name}")

    def trigger_special_effect(self, duration_ms=1500):
        """Trigger a special effect that overrides the current animation"""
        self.special_effect = CustomSparkle(pixels, WHITE, num_sparkles=25, update_interval_ms=30)
        self.special_effect_end_time = ticks_add(ticks_ms(), duration_ms)
        print("Special effect triggered!")

    def update_animations(self):
        """Update the current animation or special effect"""
        now = ticks_ms()

        # Check if special effect is active
        if self.special_effect and ticks_less(now, self.special_effect_end_time):
            self.special_effect.update()
        else:
            # Clear special effect if it expired
            if self.special_effect:
                self.special_effect = None
                print("Special effect ended")

            # Run normal animation
            if self.current_animation:
                self.current_animation.update()


state = State()


def play_sound(fname, loop=False, wait=False):
    try:
        wave_file = open("sounds/" + fname + ".wav", "rb")
        wave = audiocore.WaveFile(wave_file)
        audio.stop()
        audio.play(wave)
        if wait:
            while audio.playing:
                time.sleep(0.1)
    except Exception as e:
        print(f"Error playing sound {fname}: {e}")


async def light_animations():
    """Handle LED animations - non-blocking"""
    while True:
        # Update animations (non-blocking)
        state.update_animations()

        # Check for accelerometer tap events
        if lis3dh.tapped:
            print("Hit detected!")
            state.trigger_special_effect()

        await asyncio.sleep(0.01)  # Small delay to prevent overwhelming the CPU


async def handle_events():
    """Handle button presses and other events"""
    print("Starting event handler")
    while True:
        button_blue.update()
        button_black.update()
        button_white.update()

        if button_blue.short_count:
            print("Blue button pressed - changing color")
            state.next_color()

        if button_blue.long_press:
            state.brightness_idx = (state.brightness_idx + 1) % len(BRIGHTNESSES)
            pixels.brightness = BRIGHTNESSES[state.brightness_idx]
            print(f"Blue button long press - new brightness {new_b}")

        if button_black.short_count == 1:
            print("Black button pressed - playing sound")
            sound_idx = random.randint(0, len(SOUNDS) - 1)
            play_sound(SOUNDS[sound_idx])

        """
        if button_black.long_press:
            print("Black button long press - custom sparkle mode")
            state.animation_mode_idx = ANIMATION_MODES.index("custom_sparkle")
            state.current_animation = state.animations["custom_sparkle"]
        """

        if button_white.short_count == 1:
            print("White button pressed - changing animation")
            state.next_animation_mode()

        """
        if button_white.long_press:
            print("White button long press - comet mode")
            state.animation_mode_idx = ANIMATION_MODES.index("comet")
            state.current_animation = state.animations["comet"]
        """

        await asyncio.sleep(0.01)


async def monitor_accelerometer():
    """Monitor accelerometer for swing detection"""
    last_check = ticks_ms()

    while True:
        now = ticks_ms()

        # Only check every 100ms to avoid overwhelming
        if ticks_less(ticks_add(last_check, 100), now):
            try:
                accel_x, accel_y, accel_z = lis3dh.acceleration
                total_accel = (accel_x**2 + accel_y**2 + accel_z**2)**0.5

                if total_accel > SWING_THRESHOLD:
                    print(f"Swing detected! Acceleration: {total_accel:.2f}")
                    # Could trigger different effects here for swinging vs tapping

                last_check = now
            except Exception as e:
                print(f"Accelerometer error: {e}")

        await asyncio.sleep(0.05)


async def main():
    pixels.brightness = BRIGHTNESSES[state.brightness_idx]
    external_power.value = 1

    print("Schultuete starting up...")
    print(f"Available animations: {', '.join(ANIMATION_MODES)}")
    print("Controls:")
    print("- Blue button: Change color (long press: rainbow)")
    print("- Black button: Play sound (long press: custom sparkle)")
    print("- White button: Change animation (long press: comet)")
    print("- Tap/shake: Special effects + sounds")

    # Start with a welcome effect
    welcome_effect = CustomSparkle(pixels, VIOLET, num_sparkles=20, update_interval_ms=50)
    start_time = ticks_ms()
    while ticks_less(ticks_ms(), ticks_add(start_time, 3000)):  # 3 second welcome
        welcome_effect.update()
        await asyncio.sleep(0.01)

    print("Welcome sequence complete - starting main program")

    # Start main tasks
    main_tasks = [
        asyncio.create_task(light_animations()),
        asyncio.create_task(handle_events()),
        asyncio.create_task(monitor_accelerometer()),
    ]

    await asyncio.gather(*main_tasks)


if __name__ == "__main__":
    asyncio.run(main())
