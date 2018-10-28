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
import datetime
from xml.etree import ElementTree
from config import load_from_config

api_key = load_from_config('translink_api_key')
stops_url = "http://api.translink.ca/RTTIAPI/V1/stops/{}"
stop_estimates_url = "http://api.translink.ca/RTTIAPI/V1/stops/{}/estimates"

# Default stop number
default_stop_number = 51034 # Arbutus St at W 15 Ave


def get_next_buses(stop_number=default_stop_number, time_frame=12*60,
                   n=2, time_format="%H:%M"):
    """Returns a dictionary containing expected departure times of
    buses from specified stop.

    Example:
    >>> get_next_buses(stop_number=51034)
    (None, {'016': ['12:30', '12:41']})

    Args:
        stop_number (int): Translink bus stop number.
        time_frame (int): Maximum time in minutes that you want to
            search ahead for.
        n (int): Number of expected bus times you want to return
            (default is 2, maximum is 10).
        time_format (str): Format string for returned bus times.
            Use "%I:%M%P" for AM/PM times (e.g. '5:15pm').

    Returns:
        (error_message, leave_times): Error_message is None if the
            request was successful, otherwise a short string
            explaining why the request failed.
        leave_times (dict): If error_message is not None, this is
            a dictionary containing the expected departure times
            for the next n buses departing from the specified stop.
            There is an item for each bus route and the values
            contain departure times as strings according to
            time_format (e.g. '17:15').
    """

    params = {
        'apiKey': api_key,
        'Count': n, # The number of buses to return. Default 6
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
        # '5:15pm'
        for s in schedules:
            time_str = s.find('ExpectedLeaveTime').text

            # Translink sometimes outputs a non-standard time
            if time_str[0:3] == '24:':
                time_str = '00' + time_str[2:]

            # Convert to datetime
            t = time.strptime(time_str, "%I:%M%p")
            # Convert datetime to simple time string
            times.append(time.strftime(time_format, t))
        leave_times[route] = times

    return None, leave_times


def make_datetime(time_str, date, time_format="%H:%M"):
    """Makes a datetime object from time_str and date.

    Args:
        time_str (str): Time as string (e.g. '22:45')
        date (datetime): Date to combine time with
        time_format (str): Expected format of time_str
    """

    t = datetime.datetime.strptime(time_str, time_format).time()

    return datetime.datetime.combine(date, t)


def parse_times_into_datetimes(times, start_dt=None,
                               time_format="%H:%M"):
    """Tries to convert a squence of times into a list of
    datetimes, assuming the first time value occurs after
    current time or start_dt and each subsequent time is
    no more than 24 hours after the previous time.

    Example:
    >>> times = ['22:45', '23:30', '00:15']
    >>> parse_times_into_datetimes(times)
    [datetime.datetime(2018, 10, 28, 22, 45),
     datetime.datetime(2018, 10, 28, 23, 30),
     datetime.datetime(2018, 10, 29, 0, 15)]
    """

    if start_dt is None:
        start_dt = datetime.datetime.now()

    next_dt = make_datetime(times[0], start_dt.date(),
                            time_format=time_format)
    if (next_dt - start_dt).days < 0:
        next_dt = next_dt + datetime.timedelta(days=1)

    if len(times) > 1:
        return [next_dt] + parse_times_into_datetimes(times[1:])
    else:
        return [next_dt]


def get_next_bus_time(stop_number, bus_number=None, min_time=60*4,
                      time_format="%H:%M"):
    """Returns the bus number and expected next departure time
    from specified bus stop as strings (e.g. ('016', '18:20'))
    making sure that the next time is no sooner than min_time
    seconds from the current time.
    """

    error_message, next_buses = get_next_buses(
        stop_number=stop_number,
        n=2,
        time_format=time_format
    )
    if bus_number is None:
        bus_number = list(next_buses.keys())[0]

    if not error_message:
        try:
            next_bus_times = parse_times_into_datetimes(
                next_buses[bus_number]
            )
        except:
            logging.debug("Error finding times for bus %s (%s).",
                          '016', next_buses.__repr__())
            next_bus_time = "ERROR"

        # Either show the next bus or the second-next one
        now = datetime.datetime.now()
        i = 1 if (next_bus_times[0] - now) < \
                 datetime.timedelta(seconds=min_time) else 0

        # Convert time into simple 'HH:MM' string
        next_bus_time = next_bus_times[i].strftime(time_format)

    else:
        logging.debug("Error reading bus times: %s", error_message)
        next_bus_time = "ERROR"

    return bus_number, next_bus_time


if __name__ == "__main__":
    print(get_next_buses(*sys.argv[1:]))
