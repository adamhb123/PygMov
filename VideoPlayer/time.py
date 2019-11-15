from datetime import datetime
import pytz

utcmoment_naive = datetime.utcnow()
utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)

print("utcmoment_naive: {0}".format(utcmoment_naive))
print("utcmoment:       {0}".format(utcmoment))

localFormat = "%Y-%m-%d %H:%M:%S"

timezones = ['America/Los_Angeles', 'Europe/Berlin', 'America/Puerto_Rico']

for tz in timezones:
    localDatetime = utcmoment.astimezone(pytz.timezone(tz))
    print(localDatetime.strftime(localFormat))
