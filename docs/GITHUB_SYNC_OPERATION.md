# GitHub Sync Operation

## Deployment Topology

```txt
local runtime
→ git commit
→ git push
→ GitHub Pages
→ public dashboard
```

No local web server is required.

## Normal Runtime

Run:

```bat
runtime.bat
```

Expected output:

```txt
[SEAM] Starting persistent inference runtime...
[SEAM] starting acquisition cycle
[SEAM] sampled USGS
[SEAM] sampled EMSC
...
[SEAM] persistent manifold snapshot updated
[main xxxx] SEAM runtime delta update
git push origin main
[SEAM] sleeping 300s
```

## Git Commit Behavior

The runtime commits only changed files:

- `latest.json`
- `active_events.json`
- `data/source_logs/*`
- `data/manifolds/*`

This avoids resending stale complete datasets.
