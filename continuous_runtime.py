from pathlib import Path
import subprocess
import time

INTERVAL_SECONDS = 30

COLLECTORS = [
    "usgs.py",
    "emsc.py",
    "iris.py",
    "raspberryshake.py",
    "noaaswpc.py",
    "goes.py",
    "madis.py",
    "cwop.py",
    "uscrn.py",
    "kiwisdr.py",
    "websdr.py",
    "reversebeaconnetwork.py",
    "hamsci.py",
    "satnogs.py",
    "ecallisto.py",
    "lofar.py",
    "murchisonwidefieldarray.py",
    "allentelescopearray.py",
    "vla.py",
    "gmrt.py",
    "setilive.py",
    "nasadeepspacenetwork.py",
    "stanfordsid.py",
    "mithaystack.py",
    "berkeleyseti.py",
    "openuniversityobservatory.py",
    "sloandigitalskysurvey.py",
    "zooniverseradio.py",
    "globeatnight.py",
    "opensky.py",
    "adsbexchange.py",
    "celestrak.py",
    "safecast.py",
    "openaq.py",
    "blitzortung.py",
    "lightningmaps.py",
    "noaabuoys.py",
    "argo.py",
    "marinetraffic.py"
]

Path("data/source_logs").mkdir(parents=True, exist_ok=True)
Path("data/analysis").mkdir(parents=True, exist_ok=True)

while True:
    print("[SEAM] starting acquisition cycle")

    for collector in COLLECTORS:
        try:
            subprocess.run(["python", collector], timeout=120)
        except Exception as exc:
            print(f"[SEAM] collector failure {collector}: {exc}")

    subprocess.run(["python", "seam_engine.py"])

    subprocess.run(["git", "add", "latest.json"])
    subprocess.run(["git", "add", "active_events.json"])
    subprocess.run(["git", "add", "data/source_logs"])
    subprocess.run(["git", "add", "data/analysis"])

    commit = subprocess.run(["git", "commit", "-m", "SEAM analysis runtime update"])

    if commit.returncode == 0:
        subprocess.run(["git", "push", "origin", "main"])
    else:
        print("[SEAM] no changes to commit")

    print(f"[SEAM] sleeping {INTERVAL_SECONDS}s")
    time.sleep(INTERVAL_SECONDS)
