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
import datetime
import logging

logging.basicConfig(
	filename='logfile.txt',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logging.info("-------------- display_weather.py --------------")
logging.info("Displays current weather and next bus time to Papirus")
logging.info("LCD display.")

# Connect to Papirus LCD display
display = Papirus()

logging.info("Display size: %s", display.size)
logging.info("PIL.Image version: %s", Image.VERSION)
logging.info("numpy version: %s", np.__version__)

bitmaps.display_size = display.size

# City id for Vancouver, BC
city_id = 6173331
temp_units = u'\xb0C' # deg Celcius symbol
refresh_rate = 5*60

previous_text = None

while True:

    # First message is current date and time
    messages = [datetime.datetime.now().strftime(u"%a %b %-d, %H:%M")]

    # Get current weather conditions
    error_message, weather = current_weather.get_current_weather(city_id)

    if not error_message:
        temp = weather['main']['temp'] - 273.15
        description = weather['weather'][0]['description']
        messages.append(u"{0:.0f}{1} {2}".format(temp, temp_units, description))
    else:
        logging.debug("Error reading weather data from.")
        messages.append(u"WEATHER ERROR")

    # Get next #13 bus departure time
    bus16_no, bus16_time = bus_times.get_next_bus_time(stop_number=51034)

    # Get next #33 bus westbound departure time
    bus33_no, bus33_time = bus_times.get_next_bus_time(stop_number=61128)
    messages.append("Buses: %s @ %s, %s @ %s" % (bus16_no, bus16_time,
                                                bus33_no, bus33_time))

    text = u"\n".join(messages)
    if text != previous_text:
        im, char_count = bitmaps.display_text_prop(text,
                                                   char_set="unicode",
                                                   char_size=1)

        # Note: np.asarray(im) does not
        # currently work due to a bug in PIL

        im.putdata([p^255 for p in im.getdata()])

        display.display(im)
        display.update()
        logging.info("Display updated.")

        previous_text = text

    time.sleep(refresh_rate)

