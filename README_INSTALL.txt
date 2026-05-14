SEAM Operational Synthesis v1.2

This is a full replacement file, not a patch.

Primary change:
---------------
Adds recursive transitive convergence.

Meaning:
A ~ B and B ~ C now collapses into one canonical manifold,
even when A and C are not directly similar enough.

Expected effect:
----------------
- Brawley fragments collapse into one swarm field
- Geysers/Cobb fragments collapse into persistent geothermal field(s)
- dashboard target count should fall materially

Run:
----
python seam_operational_synthesis.py

Expected console:
-----------------
Seed events: <old local count>
Canonical events: <reduced count>
Active events: <reduced active targets>
