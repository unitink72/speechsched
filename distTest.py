import os
import drivingTime

config = {}
exec(open("settings.py").read(), config)

timeFetcher = drivingTime.DrivingTime(config)
timeFetcher.getDist('52402', '52001')
