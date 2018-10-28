#!/usr/bin/env python
"""Python module to fetch departure times from Translink's Real-Time
Transit Information API.

Includes:

get_next_buses(stop_number=default_stop_number) -> (error_message,
leave_times)

default_stop_number - set this to your favourite stop number to save
                      typing one in every time.

params              - dictionary containing various API parameters
                      including the API key to be used.

To use this module you need to register and acquire an API key
from Translink from the website link below.

Translink API Reference:
https://developer.translink.ca/ServicesRtti/ApiReference
"""

import requests
import sys
import time
from xml.etree import ElementTree
from config import load_from_config

api_key = load_from_config('translink_api_key')
stops_url = "http://api.translink.ca/RTTIAPI/V1/stops/{}"
stop_estimates_url = "http://api.translink.ca/RTTIAPI/V1/stops/{}/estimates"

# Default stop number
default_stop_number = 51034 # Arbutus St at W 15 Ave


def get_next_buses(stop_number=default_stop_number, time_frame=12*60):
    """get_next_buses(stop_number=default_stop_number) -> (error_message,
    leave_times)

    error_message is None if the request was successful or a short
    string explaining why the request failed.

    If error_messge is not None, leave_times should be a dictionary
    containing the times for the next two buses departing from the
    specified stop.

    Arguments:
    stop_number - Translink bus stop number where you want to search
                  for buses from."""

    params = {
        'apiKey': api_key,
        'Count': 2, # The number of buses to return. Default 6
        'TimeFrame': time_frame # The search time frame in minutes. Default 1440
        #'RouteNo': # If present, will search for stops specific to route
    }

    headers = {'content-type': 'application/json'}  # This doesn't work for some reason
    # Get XML instead.


    try:
        r = requests.get(stop_estimates_url.format(stop_number),
                         params=params, headers=headers)
    except requests.exceptions.ConnectionError:
        return "CONNECT ERROR", None

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        return "HTTP ERROR {}".format(r.status_code), None

    try:
        root = ElementTree.fromstring(r.content)
    except ElementTree.ParseError:
        return "PARSE ERROR", None

    error_code = None
    buses = []

    for child in root:
        if child.tag == 'Code':
            error_code = child.text
        if child.tag == 'Message':
            message = child.text
        if child.tag == 'NextBus':
            buses.append(child)

    if error_code:
        return "API ERROR {}}".format(error_code), None

    leave_times = {}

    for bus in buses:
        route = bus.find('RouteNo').text
        schedule = bus.find('Schedules')
        schedules = schedule.findall('Schedule')
        times = []

        # Date/times expected in following format
        # '5:15pm 2018-10-27'
        for s in schedules:
            time_str = s.find('ExpectedLeaveTime').text
            t = time.strptime(time_str, "%I:%M%p %Y-%m-%d")
            # Convert datetime to simple time string
            times.append(time.strftime("%Y-%m-%d %H:%M:%S", t))
        leave_times[route] = times

    return None, leave_times


if __name__ == "__main__":
    print(get_next_buses(*sys.argv[1:]))
