from pathlib import Path

SOURCES = [
    "USGS",
    "EMSC",
    "IRIS",
    "RaspberryShake",
    "NOAA_SWPC",
    "GOES",
    "MADIS",
    "CWOP",
    "USCRN",
    "KiwiSDR",
    "WebSDR",
    "ReverseBeaconNetwork",
    "HamSCI",
    "SatNOGS",
    "eCallisto",
    "LOFAR",
    "MurchisonWidefieldArray",
    "AllenTelescopeArray",
    "VLA",
    "GMRT",
    "SETILive",
    "NASADeepSpaceNetwork",
    "StanfordSID",
    "MITHaystack",
    "BerkeleySETI",
    "OpenUniversityObservatory",
    "SloanDigitalSkySurvey",
    "ZooniverseRadio",
    "GlobeAtNight",
    "OpenSky",
    "ADSBExchange",
    "Celestrak",
    "Safecast",
    "OpenAQ",
    "Blitzortung",
    "LightningMaps",
    "NOAA_Buoys",
    "ARGO",
    "MarineTraffic"
]

Path("data/source_logs").mkdir(parents=True, exist_ok=True)
Path("data/analysis").mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(exist_ok=True)
Path("cache").mkdir(exist_ok=True)

for source in SOURCES:
    Path(f"data/source_logs/{source.lower()}.ndjson").touch(exist_ok=True)

print(f"[SEAM] initialized {len(SOURCES)} raw retrieval streams")
