# Source Registry

Current expanded source pool:

| Adapter | Source |
|---|---|
| `usgs.py` | USGS |
| `emsc.py` | EMSC |
| `noaa.py` | NOAA SWPC |
| `goes.py` | GOES |
| `iris.py` | IRIS |
| `kiwisdr.py` | KiwiSDR |
| `satnogs.py` | SatNOGS |
| `blitzortung.py` | Blitzortung |
| `opensky.py` | OpenSky |
| `safecast.py` | Safecast |

## Sampling Policy

Each adapter should:

1. Pull latest available sample.
2. Preserve raw payload.
3. Add source metadata.
4. Append one NDJSON record.
5. Avoid interpretation or classification.

## Long-Term Expansion Targets

Additional sources discussed for future adapters:

- Raspberry Shake
- Reverse Beacon Network
- CWOP
- ADS-B Exchange
- Stanford SID
- e-Callisto
- MADIS
- academic/EDU public observatories
- public RF receiver networks
- radio telescope/public solar radio feeds
