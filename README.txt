SEAM Manifold Field Diagnostic

Purpose:
--------
Determine which event field actually contains
the recursive manifold lock value.

The current exporter is likely reading:
- seam_phi
or
- forecast_confidence

instead of the true manifold lock field.

Run:
----
python seam_manifold_field_diagnostic.py

Expected Output:
----------------
For each candidate field:
- present count
- unique value count
- sample values

Important:
----------
If a field shows:
- unique_values = 1
- sample_values = [1.0, 1.0, 1.0...]

then that field is NOT usable for dashboard likelihood.
