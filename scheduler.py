import time
import subprocess

COLLECTORS = [
    "usgs.py",
    "emsc.py",
    "noaa.py"
]

while True:
    for collector in COLLECTORS:
        try:
            subprocess.run(["python", collector], timeout=60)
        except Exception as e:
            print("collector error", collector, e)

    time.sleep(10)
