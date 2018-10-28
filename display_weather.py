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
import logging

logging.basicConfig(
	filename='logfile.txt',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logging.info("\n--------------- display_weather.py ---------------\n")

logging.info("Displays current weather and next bus time to LCD screen.")
logging.info("display.\n")

# Connect to Papirus LCD display
display = Papirus()

logging.info("DateTime: %s", time.strftime("%Y-%m-%d %H:%M"))
logging.info("Display size: %s", display.size)
logging.info("PIL.Image version: %s", Image.VERSION)
logging.info("numpy version: %s", np.__version__)

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
        logging.debug("Error reading weather data from.")
        messages.append(u"WEATHER ERROR")

    # Get next bus departure times
    error_message, next_buses = \
                      bus_times.get_next_buses(stop_number=51034)
    bus_number = list(next_buses.keys())[0]

    if not error_message:
        try:
            next_bus_times = [time.strptime(t, "%Y-%m-%d %H:%M:%S")
                              for t in next_buses[bus_number]]
        except:
            logging.debug("Error finding times for bus %s (%s).",
                          '016', next_buses.__repr__())
            next_bus_time = "Error"

        # Either show the next bus or the second-next one
        i = 0 if time.mktime(next_bus_times[0]) - time.time() > 60*4 else 1

        # Convert time into simple 'HH:MM' string
        next_bus_time = time.strftime("%H:%M", next_bus_times[i])

    else:
        logging.debug("Error reading bus times: %s", error_message)
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

