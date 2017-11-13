import datetime
import pytz

LOCAL_TIMEZONE = "America/Edmonton"
local_timezone = pytz.timezone(LOCAL_TIMEZONE)

d = datetime.datetime.strptime( "2007-03-04T21:08:12Z", "%Y-%m-%dT%H:%M:%SZ" )

local_time = pytz.utc.localize(d).astimezone(local_timezone).strftime('%H:%M:%S')

print(local_time)