#!/usr/bin/env python

"""Python script to display current weather conditions and next
bus time on Papirus ePaper LCD display
"""

import current_weather
import bus_times
from papirus import Papirus
import bitmaps
from PIL import Image
import numpy as np
import time
import re


print("\n--------------- display_weather.py ---------------\n")

print("Displays current weather and next bus time to LCD screen.")
print("display.\n")

# Connect to Papirus LCD display
display = Papirus()

print("DateTime: {}".format(time.strftime("%Y-%m-%d %H:%M")))
print("Display size: {}".format(display.size))
print("PIL.Image version: {}".format(Image.VERSION))
print("numpy version: {}".format(np.__version__))

bitmaps.display_size = display.size

# City id for Vancouver, BC
city_id = 6173331
tunits = u'\xb0C' # deg Celcius symbol
delay = 5*60

# Regular expression to extract time from a string
pattern = '\d{1,2}:\d{2}(am|pm)'

previous_text = None

while True:

    messages = [time.strftime(u"%a %b %-d, %H:%M")]

    # Get current weather conditions
    error_message, weather = current_weather.get_current_weather(city_id)

    if not error_message:
        temp = weather['main']['temp'] - 273.15
        description = weather['weather'][0]['description']
        messages.append(u"{0:.0f}{1} {2}".format(temp, tunits, description))
    else:
        print("Error reading weather data from.")
        messages.append(u"WEATHER ERROR")

    # Get next bus departure times
    error_message, next_buses = \
                      bus_times.get_next_buses(stop_number=51034)

    if not error_message:
        match = re.search(pattern, list(next_buses.values())[0][0])
        if match:
            next_bus_time = match.group()
        else:
            print("Error understanding bus time string '{s}'".format(next_buses))
            next_bus_time = "Error"
    else:
        print("Error reading bus times:", error_message)
        next_bus_time = "Error"

    messages.append("Next bus: {}".format(next_bus_time))

    text = u"\n".join(messages)
    if text != previous_text:
        im, char_count = bitmaps.display_text_prop(text,
                                                   char_set="unicode",
                                                   char_size=2)

        # Note: np.asarray(im) does not
        # currently work due to a bug in PIL

        im.putdata([p^255 for p in im.getdata()])

        display.display(im)
        display.update()

        previous_text = text

    time.sleep(delay)

