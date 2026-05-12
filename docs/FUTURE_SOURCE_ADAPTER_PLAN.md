# Future Source Adapter Plan

The current system samples placeholder latest observations for expanded sources.

Next step is replacing placeholder payloads with real raw payload fetches while preserving the adapter contract.

## Priority Adapters

1. USGS real-time feeds
2. EMSC global seismic feed
3. NOAA SWPC feeds
4. GOES solar/X-ray/proton feeds
5. IRIS waveform/event metadata
6. KiwiSDR public receiver metadata/feed snapshots
7. SatNOGS observations
8. Blitzortung lightning feed
9. OpenSky state vectors
10. Safecast radiation observations

## Adapter Rule

Do not interpret. Preserve raw.

```txt
fetch → timestamp → append → exit
```

SEAM runtime performs inference later.
