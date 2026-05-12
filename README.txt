Extract directly into:

C:\CleanRoom

Replace:
continuum_dual_acquisition_runtime.py

Add:
source_health_quarantine.py

Fixes included:
- parallel acquisition
- 32 concurrent workers
- true 1s connect timeout
- true 1s read timeout
- retries disabled
- redirects disabled
- source quarantine support
- eliminates serial blocking

Expected runtime reduction:
~90s -> ~10-20s
