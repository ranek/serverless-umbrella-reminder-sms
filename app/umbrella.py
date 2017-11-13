import boto3
import os
import random
import re
from botocore.vendored import requests
from datetime import datetime
import pytz
import itertools

PHONE_NUMBER = os.environ['PHONE_NUMBER']
WEATHER_LOCATION = os.environ['WEATHER_LOCATION']
TIME_ZONE = os.environ['TIME_ZONE']
DARK_SKY_KEY = os.environ['DARK_SKY_KEY']
MESSAGE_LOCAL_TIME = os.environ['MESSAGE_LOCAL_TIME']

time_zone = pytz.timezone(TIME_ZONE)

# Force connection to us-west-2, since not all regions support SMS
sns_client = boto3.client('sns', region_name='us-west-2')


def get_forecast(dark_sky_key, location):
    return requests.get("https://api.darksky.net/forecast/%s/%s?units=si" %
                        (dark_sky_key, location)).json()


def localize(time):
    return pytz.utc.localize(time).astimezone(time_zone)


def hour_to_hour(hour):
    return localize(datetime.fromtimestamp(hour * 3600)).strftime('%-H:%M')


def ranges(i):
    for offset, hours in itertools.groupby(
            enumerate(i), lambda v: v[1] - v[0]):
        h = list(hours)
        start_hour = h[0][1]
        end_hour = h[-1][1]

        if start_hour == end_hour:
            yield "at %s" % hour_to_hour(start_hour)
        else:
            yield "from %s to %s" % (hour_to_hour(start_hour),
                                     hour_to_hour(end_hour + 1))


def get_raininess_message(hourly_data, threshold):
    rainy_hours = list(
        filter(lambda h: h['precipIntensity'] > threshold, hourly_data))

    hourly = [int(h['time']) / 3600 for h in rainy_hours]
    rainy = list(ranges(hourly))

    if len(rainy) == 0:
        return None
    elif len(rainy) == 1:
        return "%s" % rainy[0]
    elif len(rainy) == 2:
        return " and ".join(rainy)
    else:
        return '%s, and %s' % (', '.join(rainy[:-1]), rainy[-1])


def get_alert(forecast):

    if forecast['timezone'] != TIME_ZONE:
        print(
            "WARNING: Your specified time zone, %s, may not match forecast timezone, %s."
            % (TIME_ZONE, forecast['timezone']))

    hourly_data = forecast['hourly']['data'][:18]
    rainy = get_raininess_message(hourly_data, 0.5)
    heavy_rain = get_raininess_message(hourly_data, 1.5)

    if heavy_rain:
        return "Don't forget your umbrella! Heavy rain today %s. Showers %s." % (
            heavy_rain, rainy)
    elif rainy:
        return "No heavy rain today, but showers %s." % (rainy)
    else:
        return None


def lambda_handler(event, context):
    t = datetime.strptime(event['time'], "%Y-%m-%dT%H:%M:%SZ")
    local_time = localize(t).strftime('%H:%M')

    print("Got event notification for time %s, which is %s local." %
          (event['time'], local_time))

    if local_time == MESSAGE_LOCAL_TIME:
        print("Checking forecast for the day.")
        alert = get_alert(get_forecast(DARK_SKY_KEY, WEATHER_LOCATION))

        if alert:
            print("Sending alert: %s" % alert)
            response = sns_client.publish(
                PhoneNumber=PHONE_NUMBER, Message=alert)
        else:
            print("Looks like clear skies today!")
