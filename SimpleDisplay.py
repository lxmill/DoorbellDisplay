# This example implements a simple two line scroller using
# Adafruit_CircuitPython_Display_Text. Each line has its own color
# and it is possible to modify the example to use other fonts and non-standard
# characters.

import adafruit_display_text.label
import board
import busio
import displayio
import framebufferio
import rgbmatrix
import time

import helper

from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.network import Network
from adafruit_esp32spi import adafruit_esp32spi

from rtc import RTC
import digitalio


def DesUpdate():
    TEXT_URL = "https://mill.pt/matrix/display_data.php"  # URL to results page

    print("Fetching text from", TEXT_URL)
    # r = requests.get(TEXT_URL)
    r = network.fetch_data(TEXT_URL)

    print("Text recovered: ", r)

    lines = (r).split("<br>")

    # Initialize variables
    text_info = None
    color_info = None
    speed_info = None
    fontOption = None

    # Loop through each line and extract the values
    for line in lines:
        parts = line.split(":")  # Split each line by ':' to separate key and value
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            if key == "Text":
                text_info = value
            elif key == "Hexadecimal":
                result_string = value[1:]
                hex_number = int(result_string, 16)
                color_info = hex_number
                print("Color HEX: ", color_info)
            elif key == "Float":
                speed_info = float(value)  # Convert the value to a float
            elif key == "Option":
                fontOption = value
    # Print the extracted values
    print("Text:", text_info)
    print("Hexadecimal:", color_info)
    print("Float:", speed_info)
    print("Font:", fontOption)

    return [text_info, color_info, speed_info, fontOption]


# This function will move the hand forward and backwards
def handSlide(forward):
    display.show(doorbell)
    if bg_hand.x == 15:
        forward = False
    if bg_hand.x == 6:
        forward = True
    if forward:
        bg_hand.x += 1
    else:
        bg_hand.x -= 1
    time.sleep(0.1)
    return forward


# This function will scoot one label a pixel to the left and send it back to
# the far right if it's gone all the way off screen.
def scroll(line, delay):
    # time.sleep(delay)
    # line.x = line.x - 1
    # line_width = line.bounding_box[2]
    # if line.x < -line_width:
    #     line.x = display.width
    line_width = line.bounding_box[2]
    while line.x > -line_width:
        line.x = line.x - 1
        time.sleep(delay)
    line.x = display.width


# If there was a display before (protomatter, LCD, or E-paper), release it so
# we can create ours
displayio.release_displays()

# This next call creates the RGB Matrix object itself. It has the given width
# and height. bit_depth can range from 1 to 6; higher numbers allow more color
# shades to be displayed, but increase memory usage and slow down your Python
# code. If you just want to show primary colors plus black and white, use 1.
# Otherwise, try 3, 4 and 5 to see which effect you like best.

# If you have a 16x32 display, try with just a single line of text.
matrix = rgbmatrix.RGBMatrix(
    width=32,
    bit_depth=4,
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2,
    ],
    addr_pins=[board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE,
)

cwd = ("/" + __file__).rsplit("/", 1)[
    0
]  # the current working directory (where this file is)

# Text Fonts
Verdana_font = cwd + "/fonts/verdana-7pt.bdf"
RobotoMono_font = cwd + "/fonts/RobotoMono-Bold-7pt.bdf"
Tahoma_font = cwd + "/fonts/tahoma-7pt.bdf"
l_10646_font = cwd + "/fonts/l_10646-7pt.bdf"
ter_font = cwd + "/fonts/ter-u12n.bdf"
NotoSansMediumStrip_font = cwd + "/fonts/NotoSans-Medium-strip-10px.bdf"

small_font = cwd + "/fonts/spleen-6x12.bdf"
cust_font = cwd + "/fonts/04B_03__7pt.bdf"
tiny_font = cwd + "/fonts/spleen-5x8.bdf"

fontVerdana = bitmap_font.load_font(Verdana_font)
fontRobotoMono = bitmap_font.load_font(RobotoMono_font)
fontTahoma = bitmap_font.load_font(Tahoma_font)
font_l_10646 = bitmap_font.load_font(l_10646_font)
font_ter = bitmap_font.load_font(ter_font)
font_NotoSansMediumStrip = bitmap_font.load_font(NotoSansMediumStrip_font)

fontSmall = bitmap_font.load_font(small_font)
fontTiny = bitmap_font.load_font(tiny_font)
fontCust = bitmap_font.load_font(cust_font)

# Associate the RGB matrix with a Display so that we can use displayio features
display = framebufferio.FramebufferDisplay(matrix)

# While preaparing the environment displays an image in the display
splash = displayio.Group()
background = displayio.OnDiskBitmap("RGB_TRI.bmp")
bg_sprite = displayio.TileGrid(background, pixel_shader=background.pixel_shader)

splash.append(bg_sprite)
display.show(splash)

# Get Wi-Fi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = digitalio.DigitalInOut(board.ESP_CS)
esp32_ready = digitalio.DigitalInOut(board.ESP_BUSY)
esp32_reset = digitalio.DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
# requests.set_socket(socket, esp)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])

# Scan the networks avaiable
for ap in esp.scan_networks():
    print("\t%s\t\tRSSI: %d" % (str(ap["ssid"], "utf-8"), ap["rssi"]))

while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
        print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
        print("My IP address is", esp.pretty_ip(esp.ip_address))
    except OSError as e:
        print("could not connect to AP, retrying: ", e)

# Funcionamento de manutenção
network = Network(status_neopixel=board.NEOPIXEL, esp=esp)

# network = Network(status_neopixel=board.NEOPIXEL)

text_info, color_info, speed_info, fontOption = DesUpdate()

fontMedium = None
if fontOption == "Verdana":
    fontMedium = fontVerdana
elif fontOption == "RobotoMono-Bold":
    fontMedium = fontRobotoMono
elif fontOption == "Tahoma":
    fontMedium = fontTahoma
elif fontOption == "l_10646":
    fontMedium = font_l_10646
elif fontOption == "ter-u12n":
    fontMedium = font_ter
elif fontOption == "NotoSansMediumStrip":
    fontMedium = font_NotoSansMediumStrip
else:
    print("Unknown font!")

if "\n" in text_info:
    modified_string = text_info.replace("\n", "   ")
else:
    modified_string = text_info

# Info to display: DATE / TIME / [OPEN/CLOSE] / DESCRIPTION
Date = adafruit_display_text.label.Label(fontTiny, color=0xFF0000)
Date.x = 1
Date.y = 4

Time = adafruit_display_text.label.Label(fontSmall, color=0x0080FF)
Time.x = 1
Time.y = 12

open_close = adafruit_display_text.label.Label(fontCust, color=0x00FF00)

Description = adafruit_display_text.label.Label(fontMedium)
Description.x = 1
Description.y = 3
# Description.text = "MILL - Makers In Little Lisbon"
Description.text = modified_string
Description.color = color_info

# Create groups with each frame: [DATE + TIME] / [OPEN/CLOSE + DESCRIPTION] / [HANDBELL] / [X_SIGN]
date_time = displayio.Group()
date_time.append(Date)
date_time.append(Time)

state_description = displayio.Group()
state_description.append(Description)
state_description.append(open_close)

doorbell = displayio.Group()
handPointer = displayio.OnDiskBitmap("handPointer.bmp")
bg_hand = displayio.TileGrid(handPointer, pixel_shader=handPointer.pixel_shader)
bg_hand.x = 7
doorbell.append(bg_hand)

x_sign = displayio.Group()
Xpointer = displayio.OnDiskBitmap("X_bmp.bmp")
bg_X = displayio.TileGrid(Xpointer, pixel_shader=Xpointer.pixel_shader)
x_sign.append(bg_X)

# Variables for the flow of the environment
## Opendays (Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday)
openDays = [0, 1, 1, 1, 1, 1, 0]

# Initialize a variable to keep track of the last time the action was performed
last_action_time = None
stateAction_time = None

# Define the interval in seconds
interval = 8
intervalState = 30
localtime_refresh = None

# Possible actions groups to display
actions = ["date_time", "state_description", "doorbell"]
number_actions = len(actions)

index = 0
state = actions[index]

open_close_sign = None

override_CloseOpen = False

forward = True

# Initialize the button as a digital input with a pull-up resistor
button_up = digitalio.DigitalInOut(board.BUTTON_UP)
button_up.direction = digitalio.Direction.INPUT
button_up.pull = digitalio.Pull.UP

# Initialize the button as a digital input with a pull-up resistor
button_down = digitalio.DigitalInOut(board.BUTTON_DOWN)
button_down.direction = digitalio.Direction.INPUT
button_down.pull = digitalio.Pull.UP

delay = 0.03

while True:
    # only query the online time once per hour (and on first run)
    if (not localtime_refresh) or (time.monotonic() - localtime_refresh) > 3600:
        try:
            print("Getting time from internet!")
            network.get_local_time()
            localtime_refresh = time.monotonic()
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)
            continue

    # Check if the specified interval has passed and the define the action group to be displayed
    if (not last_action_time) or (time.monotonic() - last_action_time >= interval):
        index += 1

        if index == number_actions:
            index = 0

        state = actions[index]

        # Update the last action time
        last_action_time = time.monotonic()

    # Check if the specified interval has passed and verifies the state of the MILL
    if (not stateAction_time) or (time.monotonic() - stateAction_time >= intervalState):
        if (
            (openDays[time.localtime().tm_wday] == 1)
            and (time.localtime().tm_hour >= 10)
            and (time.localtime().tm_hour < 19)
            and not override_CloseOpen
        ):
            print("Normal")
            # OPENDAY
            open_close.text = "OPEN"
            open_close.color = 0x00FF00
            open_close.x = 5
            open_close.y = 12
            open_close_sign = True
        else:
            # # CLOSEDAY
            open_close.text = "CLOSED"
            open_close.color = 0xFF0000
            open_close.x = 0
            open_close.y = 12
            open_close_sign = False

        # Update the last action time variable
        stateAction_time = time.monotonic()

    if not button_down.value:
        print("Button Down")
        display.show(splash)
        text_info, color_info, speed_info, fontOption = DesUpdate()

        if fontOption == "Verdana":
            fontMedium = fontVerdana
        elif fontOption == "RobotoMono-Bold":
            fontMedium = fontRobotoMono
        elif fontOption == "Tahoma":
            fontMedium = fontTahoma
        elif fontOption == "l_10646":
            fontMedium = font_l_10646
        elif fontOption == "ter-u12n":
            fontMedium = font_ter
        elif fontOption == "NotoSansMediumStrip":
            fontMedium = font_NotoSansMediumStrip
        else:
            print("Unknown font!")

        modified_string = None
        if "\n" in text_info:
            modified_string = text_info.replace("\n", "   ")
        else:
            modified_string = text_info

        Description.text = modified_string
        Description.color = color_info
        Description.font = fontMedium
        # delay = speed_info

        # time.sleep(0.5)

    if not button_up.value:
        print("Override")
        display.show(splash)
        time.sleep(1)
        override_CloseOpen = not override_CloseOpen
        open_close_sign = not open_close_sign

        if open_close_sign:
            # OPENDAY
            open_close.text = "OPEN"
            open_close.color = 0x00FF00
            open_close.x = 5
            open_close.y = 12
        else:
            # CLOSEDAY
            open_close.text = "CLOSED"
            open_close.color = 0xFF0000
            open_close.x = 0
            open_close.y = 12

    # Display group [DATE + TIME]
    if state == actions[0]:
        Date.text = helper.date(RTC().datetime)
        Time.text = helper.hh_mm(RTC().datetime)

        display.show(date_time)
        time.sleep(1)

    # Display group [OPEN/CLOSE + DESCRIPTION]
    if state == actions[1]:
        display.show(state_description)
        scroll(Description, delay)

    # Display group [HAND_POINTER][X_SIGN]
    if state == actions[2]:
        if open_close_sign:
            forward = handSlide(forward)
        elif not open_close_sign:
            x_sign.x = 8
            display.show(x_sign)

    # Refresh the screen
    display.refresh(minimum_frames_per_second=0)
