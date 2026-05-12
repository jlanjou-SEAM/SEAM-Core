# Delta Sync Change

Previous behavior:
rewrite complete runtime state every cycle

New behavior:
append-only source acquisition
delta git commits only
snapshot regeneration local-side

This reduces:
- Git history bloat
- bandwidth
- stale retransmission
- GitHub Pages rebuild load
