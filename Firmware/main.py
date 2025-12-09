# code.py -- MacroPad firmware with config.json, server-merge via USB serial
import board
import digitalio
import busio
import neopixel
import usb_hid
import supervisor
import sys
import json
import time
import adafruit_ssd1306

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS

# -----------------------
# Hardware configuration
# -----------------------
SWITCH_PINS = [
    board.GP1,  # S1
    board.GP2,  # S2
    board.GP4,  # S3 (modifier for layer switching)
    board.GP3,  # S4
    board.GP0   # S5
]

NUM_LEDS = 2
NEOPIXEL_PIN = board.GP26

# OLED (I2C default pins)
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
oled.fill(0)
oled.show()

# Neopixels (SK6812-Mini-E often uses GRB)
leds = neopixel.NeoPixel(NEOPIXEL_PIN, NUM_LEDS, auto_write=True, pixel_order=neopixel.GRB)

# HID
kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)

# -----------------------
# Defaults / config file
# -----------------------
CONFIG_PATH = "/config.json"

DEFAULT_CONFIG = {
    "macro_layers": [
        {
            "type": "macro",
            "name": "Edit",
            "number": 1,
            "keycodes": {
                "1": [ { "action": "send", "keys": ["CONTROL", "X"] } ],
                "2": [ { "action": "send", "keys": ["CONTROL", "C"] } ],
                "3": [ { "action": "send", "keys": ["CONTROL", "V"] } ],
                "4": [ { "action": "send", "keys": ["CONTROL", "Z"] } ],
                "5": [ { "action": "send", "keys": ["CONTROL", "Y"] } ]
            }
        },
        {
            "type": "macro",
            "name": "Git",
            "number": 2,
            "keycodes": {
                "1": [ { "action": "write", "text": "git add ." } ],
                "2": [ { "action": "write", "text": "git commit -m \"\"" } ],
                "3": [ { "action": "write", "text": "git push origin main" } ],
                "4": [ { "action": "write", "text": "git pull" } ],
                "5": [ { "action": "write", "text": "git init" } ]
            }
        },
        {
            "type": "macro",
            "name": "Snip",
            "number": 3,
            "keycodes": {
                "1": [
                    { "action": "write", "text": "try:" },
                    { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "..." },
                    { "action": "press", "key": "ENTER" },
                    { "action": "press", "key": "BACKSPACE" },
                    { "action": "write", "text": "except:" },
                    { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "..." }
                ],
                "2": [ { "action": "write", "text": "while True:" }, { "action": "press", "key": "ENTER" }, { "action": "write", "text": "..." } ],
                "3": [ { "action": "write", "text": "def main():" }, { "action": "press", "key": "ENTER" }, { "action": "write", "text": "..." } ],
                "4": [
                    { "action": "write", "text": "if ...:" }, { "action": "press", "key": "ENTER" }, { "action": "write", "text": "..." },
                    { "action": "press", "key": "BACKSPACE" },
                    { "action": "write", "text": "elif ...:" }, { "action": "press", "key": "ENTER" }, { "action": "write", "text": "..." },
                    { "action": "press", "key": "BACKSPACE" },
                    { "action": "write", "text": "else:" }, { "action": "press", "key": "ENTER" }, { "action": "write", "text": "..." }
                ],
                "5": [
                    { "action": "write", "text": "from time import sleep as delay" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "if __name__ == \"__main__\":" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "while True:" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "try:" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "main()" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "except KeyboardInterrupt:" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "print(\"\\nGoodbye\", end=\"\", flush=True)" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "delay(0.5)" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "print(\".\", end=\"\", flush=True)" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "delay(0.5)" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "print(\".\")" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "delay(0.5)" }, { "action": "press", "key": "ENTER" },
                    { "action": "write", "text": "exit(0)" }, { "action": "press", "key": "ENTER" }
                ]
            }
        },
        {
            "type": "macro",
            "name": "Win",
            "number": 4,
            "keycodes": {
                "1": [ { "action": "send", "keys": ["GUI", "UP_ARROW"] } ],
                "2": [ { "action": "send", "keys": ["GUI", "LEFT_ARROW"] } ],
                "3": [ { "action": "send", "keys": ["GUI", "D"] } ],
                "4": [ { "action": "send", "keys": ["GUI", "RIGHT_ARROW"] } ],
                "5": [ { "action": "send", "keys": ["GUI", "DOWN_ARROW"] } ]
            }
        }
    ],
    "screen_layers": [
        { "type": "screen", "name": "Edit", "number": 1, "screen": { "line1": "EDIT", "line2": "" } },
        { "type": "screen", "name": "GIT", "number": 2, "screen": { "line1": "GIT", "line2": "" } },
        { "type": "screen", "name": "SNIP", "number": 3, "screen": { "line1": "SNIP", "line2": "" } },
        { "type": "screen", "name": "WIN",  "number": 4, "screen": { "line1": "WIN",  "line2": "" } }
    ]
}

# -----------------------
# Globals & status
# -----------------------
# Load switches
switches = []
for p in SWITCH_PINS:
    sw = digitalio.DigitalInOut(p)
    sw.direction = digitalio.Direction.INPUT
    sw.pull = digitalio.Pull.UP
    switches.append(sw)

# LED colors
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (255, 0, 0)
COLOR_BLUE  = (0, 0, 255)
COLOR_RED   = (0, 255, 0)

# Status flags
macro_triggered = False
macro_error = False
macro_layer_changing = False
screen_layer_changing = False
layer_error = False

# Layer pointers
macro_layers = []
screen_layers = []
current_macro_index = 0  # index into macro_layers list
current_screen_index = 0

# prev button states for edge detection
prev_states = [False] * 5

# -----------------------
# Helpers: config IO
# -----------------------
def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f)
        return True
    except Exception as e:
        print("SAVE_CONFIG_ERR", e)
        return False

def load_config():
    global macro_layers, screen_layers, current_macro_index, current_screen_index
    try:
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
    except Exception:
        cfg = DEFAULT_CONFIG
        save_config(cfg)

    # Normalize lists (ensure proper types)
    macro_layers = cfg.get("macro_layers", [])
    screen_layers = cfg.get("screen_layers", [])

    # sort by number for deterministic ordering
    macro_layers.sort(key=lambda x: int(x.get("number", 0)))
    screen_layers.sort(key=lambda x: int(x.get("number", 0)))

    # clamp current indices
    if not macro_layers:
        macro_layers = DEFAULT_CONFIG["macro_layers"]
    if not screen_layers:
        screen_layers = DEFAULT_CONFIG["screen_layers"]

    current_macro_index = 0
    current_screen_index = 0

    return cfg

# initial load
config = load_config()

# -----------------------
# Helpers: LED / OLED
# -----------------------
def set_led0_color(col):
    leds[0] = col

def set_led1_color(col):
    leds[1] = col

def update_leds_status():
    # LED 0 - macro status
    if macro_error:
        leds[0] = COLOR_RED
    elif macro_triggered:
        leds[0] = COLOR_GREEN
    else:
        leds[0] = COLOR_WHITE

    # LED 1 - layer status
    if layer_error:
        leds[1] = COLOR_RED
    elif macro_layer_changing:
        leds[1] = COLOR_GREEN
    elif screen_layer_changing:
        leds[1] = COLOR_BLUE
    else:
        leds[1] = COLOR_WHITE

def update_oled_for_current_screen():
    oled.fill(0)
    try:
        macro = macro_layers[current_macro_index]
        macro_name = str(macro.get("name", ""))
        scr = screen_layers[current_screen_index]
        lines = scr.get("screen", {})
        oled.text(macro_name, 0, 0, 1)
        oled.text(str(lines.get("line1","")), 0, 16, 1)
        oled.text(str(lines.get("line2","")), 0, 32, 1)
    except Exception:
        oled.text("ERR", 0, 0, 1)
    oled.show()

update_leds_status()
update_oled_for_current_screen()

# -----------------------
# Helpers: Keycode mapping
# -----------------------
# Map string names to Keycode attributes for common keys.
KEYCODE_MAP = {
    "A": Keycode.A, "B": Keycode.B, "C": Keycode.C, "D": Keycode.D,
    "E": Keycode.E, "F": Keycode.F, "G": Keycode.G, "H": Keycode.H,
    "I": Keycode.I, "J": Keycode.J, "K": Keycode.K, "L": Keycode.L,
    "M": Keycode.M, "N": Keycode.N, "O": Keycode.O, "P": Keycode.P,
    "Q": Keycode.Q, "R": Keycode.R, "S": Keycode.S, "T": Keycode.T,
    "U": Keycode.U, "V": Keycode.V, "W": Keycode.W, "X": Keycode.X,
    "Y": Keycode.Y, "Z": Keycode.Z,

    "1": Keycode.ONE, "2": Keycode.TWO, "3": Keycode.THREE, "4": Keycode.FOUR,
    "5": Keycode.FIVE, "6": Keycode.SIX, "7": Keycode.SEVEN, "8": Keycode.EIGHT,
    "9": Keycode.NINE, "0": Keycode.ZERO,

    "ENTER": Keycode.ENTER,
    "BACKSPACE": Keycode.BACKSPACE,
    "TAB": Keycode.TAB,
    "SPACE": Keycode.SPACE,
    "ESCAPE": Keycode.ESCAPE,

    "UP_ARROW": Keycode.UP_ARROW,
    "DOWN_ARROW": Keycode.DOWN_ARROW,
    "LEFT_ARROW": Keycode.LEFT_ARROW,
    "RIGHT_ARROW": Keycode.RIGHT_ARROW,

    "CONTROL": Keycode.CONTROL,
    "SHIFT": Keycode.SHIFT,
    "ALT": Keycode.ALT,
    "GUI": Keycode.GUI,

    "D": Keycode.D,  # used in Win+D
    # add more if you need...
}

def keycode_from_name(name):
    # Accept either direct KEYCODE_MAP entries, or single characters (use layout.write)
    if not isinstance(name, str):
        return None
    n = name.upper()
    return KEYCODE_MAP.get(n, None)

# -----------------------
# Helpers: Macro execution
# -----------------------
def execute_macro_actions(action_list):
    global macro_error
    try:
        for step in action_list:
            typ = step.get("action")
            if typ == "send":
                keys = step.get("keys", [])
                codes = []
                for k in keys:
                    kc = keycode_from_name(k)
                    if kc is None:
                        # fallback: if single char, write it
                        if isinstance(k, str) and len(k) == 1:
                            layout.write(k)
                        else:
                            # unknown key name
                            print("UNKNOWN_KEY", k)
                    else:
                        codes.append(kc)
                if codes:
                    kbd.send(*codes)
                time.sleep(0.01)
            elif typ == "press":
                k = step.get("key")
                kc = keycode_from_name(k)
                if kc is not None:
                    kbd.send(kc)
                else:
                    # fallback to write single char if that was provided
                    if isinstance(k, str) and len(k) == 1:
                        layout.write(k)
                    else:
                        print("UNKNOWN_PRESS", k)
                time.sleep(0.01)
            elif typ == "write":
                txt = step.get("text", "")
                if txt:
                    layout.write(str(txt))
                time.sleep(0.01)
            else:
                print("UNKNOWN_ACTION", typ)
        # small settle delay
        time.sleep(0.02)
    except Exception as e:
        print("MACRO_EXEC_ERR", e)
        macro_error = True

# -----------------------
# Helpers: Config merge (server packet processing)
# -----------------------
def apply_server_packet(packet):
    global config, macro_layers, screen_layers
    t = packet.get("type")
    num = int(packet.get("number", -1))
    if t == "macro":
        # replace same-number macro layer (or append)
        macro_layers = [m for m in macro_layers if int(m.get("number", -1)) != num]
        macro_layers.append(packet)
        macro_layers.sort(key=lambda x: int(x.get("number", 0)))
    elif t == "screen":
        screen_layers = [s for s in screen_layers if int(s.get("number", -1)) != num]
        screen_layers.append(packet)
        screen_layers.sort(key=lambda x: int(x.get("number", 0)))
    else:
        print("BAD_PACKET_TYPE", t)
        return False

    # write back to disk
    new_cfg = { "macro_layers": macro_layers, "screen_layers": screen_layers }
    success = save_config(new_cfg)
    if success:
        # reload local variables from disk
        load_config()
        print("CONFIG_APPLIED")
    return success

def try_read_serial_json():
    # Non-blocking check for new JSON line on USB serial.
    # If present, read a full line (blocking) and parse as JSON.
    # Host should send one-line JSON followed by newline.
    try:
        if supervisor.runtime.serial_bytes_available:
            raw = sys.stdin.readline().strip()
            if not raw:
                return False
            try:
                packet = json.loads(raw)
            except Exception as e:
                print("BAD_JSON", e)
                return False
            return apply_server_packet(packet)
    except Exception as e:
        print("SERIAL_READ_ERR", e)
    return False

# -----------------------
# Main loop helpers
# -----------------------
def get_current_macro_layer():
    if not macro_layers:
        return None
    return macro_layers[current_macro_index]

def get_key_actions_for_button(idx):
    # idx is 0..4 for S1..S5. config uses "1".."5"
    layer = get_current_macro_layer()
    if not layer:
        return []
    keymap = layer.get("keycodes", {})
    return keymap.get(str(idx+1), [])

# initialize prev states
prev_states = [False]*5

# -----------------------
# Main loop
# -----------------------
print("READY")
while True:
    # Poll serial for config updates (only when available)
    try_read_serial_json()

    # reset flags each loop
    macro_triggered = False
    macro_error = False
    macro_layer_changing = False
    screen_layer_changing = False
    layer_error = False

    pressed = [not sw.value for sw in switches]  # True when pressed

    # Layer switching when S3 held (index 2)
    if pressed[2]:
        # Macro layer back/forward (S2 index 1, S4 index 3)
        if pressed[1] and not prev_states[1]:
            macro_layer_changing = True
            current_macro_index = (current_macro_index - 1) % len(macro_layers)
            update_leds_status()
            update_oled_for_current_screen()
            time.sleep(0.18)
            # consume this event
        elif pressed[3] and not prev_states[3]:
            macro_layer_changing = True
            current_macro_index = (current_macro_index + 1) % len(macro_layers)
            update_leds_status()
            update_oled_for_current_screen()
            time.sleep(0.18)

        # Screen layer back/forward (S1 index 0, S5 index 4)
        if pressed[0] and not prev_states[0]:
            screen_layer_changing = True
            current_screen_index = (current_screen_index - 1) % len(screen_layers)
            update_leds_status()
            update_oled_for_current_screen()
            time.sleep(0.18)
        elif pressed[4] and not prev_states[4]:
            screen_layer_changing = True
            current_screen_index = (current_screen_index + 1) % len(screen_layers)
            update_leds_status()
            update_oled_for_current_screen()
            time.sleep(0.18)

    else:
        # Only trigger macros when S3 not held
        for i, state in enumerate(pressed):
            if state and not prev_states[i]:
                # run macro for button i
                actions = get_key_actions_for_button(i)
                if actions:
                    macro_triggered = True
                    update_leds_status()
                    execute_macro_actions(actions)
                    # small visible/settle time so LED shows
                    time.sleep(0.05)
                    macro_triggered = False
                else:
                    # no macro assigned -> do nothing (or beep if you add one)
                    pass

    update_leds_status()
    prev_states = pressed
    time.sleep(0.04)
