SEAM Recursive Ingestion Fix v2.0

Critical Runtime Fix
--------------------
The unified field builder was incorrectly ingesting:
    files

instead of:
    observations inside files

Result:
    52 observations total
    1 seed event
    1 canonical event

This package restores:
    recursive payload extraction

The builder now recursively extracts:
- GeoJSON FeatureCollections
- features[]
- entries[]
- observations[]
- events[]
- stations[]
- records[]
- nested arrays
- nested payload objects

Expected Runtime Recovery
-------------------------
Before fix:
    Observations: 52

After fix:
    Observations: 100000+

Expected operational recovery:
    Seed events: 40-120
    Canonical events: 5-15

Install
-------
Replace:
    seam_unified_recursive_field_builder.py

Optional:
    replace SEAM_Run_Update.bat
