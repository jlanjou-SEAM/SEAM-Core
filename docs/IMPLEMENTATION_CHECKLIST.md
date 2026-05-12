# Implementation Checklist

## One-Time Setup

- [ ] Extract current runtime package into repo root.
- [ ] Confirm `runtime.bat` exists.
- [ ] Confirm `continuous_runtime.py` exists.
- [ ] Confirm `runtime/manifold_registry.py` exists.
- [ ] Confirm collector files exist.
- [ ] Confirm `latest.json` exists.
- [ ] Confirm `active_events.json` exists.
- [ ] Confirm `.github/workflows/deploy.yml` is removed unless PAT has workflow scope.

## Runtime Verification

Run:

```bat
runtime.bat
```

Confirm:

- [ ] source adapters sample successfully
- [ ] no Python tracebacks
- [ ] persistent manifold snapshot updates
- [ ] git commit succeeds
- [ ] git push succeeds
- [ ] runtime sleeps 300 seconds

## Dashboard Verification

Open:

```txt
https://jlanjou-seam.github.io/SEAM-Core/
```

Confirm:

- [ ] TARGET cards persist
- [ ] likelihood is sorted descending
- [ ] high likelihood is red/orange
- [ ] TARGET state is red/locked
- [ ] no stale demo events
- [ ] refresh countdown works
