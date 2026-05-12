# Persistent SEAM Target Pipeline

raw stream collectors
→ append NDJSON
→ seam_engine.py
→ persistent target registry
→ lock reinforcement
→ ETA synthesis
→ latest.json
→ active_events.json
→ git delta sync
→ GitHub Pages render

New persistent registry:

data/analysis/target_registry.json

Tracks:

- lock acquisition
- lock age
- persistence cycles
- target centroid
- ETA windows
- event probability
- coherence
- lock confidence
