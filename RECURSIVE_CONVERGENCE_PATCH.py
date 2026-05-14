"""
SEAM Recursive Convergence Patch v1.0

Drop-in logic additions for seam_operational_synthesis.py

Purpose:
--------
Add recursive manifold convergence AFTER seed generation.

Fixes:
------
- swarm fragmentation
- duplicate regional manifolds
- over-segmentation

Examples:
---------
Brawley swarm
The Geysers swarm
Cobb geothermal field
"""

# ============================================================
# RECURSIVE CONVERGENCE
# ============================================================

def manifold_distance_km(a, b):

    import math

    lat1 = a.get("latitude", 0.0)
    lon1 = a.get("longitude", 0.0)

    lat2 = b.get("latitude", 0.0)
    lon2 = b.get("longitude", 0.0)

    dlat = lat1 - lat2
    dlon = lon1 - lon2

    return ((dlat*dlat + dlon*dlon) ** 0.5) * 111.0


def recursive_similarity(a, b):

    score = 0.0

    # Same regime.
    if a.get("regime") == b.get("regime"):
        score += 0.30

    # Signature continuity.
    if a.get("signature") == b.get("signature"):
        score += 0.20

    # Spatial continuity.
    distance = manifold_distance_km(a, b)

    if distance < 15:
        score += 0.30

    elif distance < 40:
        score += 0.15

    # Trajectory continuity.
    if a.get("course") == b.get("course"):
        score += 0.10

    # Density continuity.
    obs_a = a.get("observation_count", 0)
    obs_b = b.get("observation_count", 0)

    if max(obs_a, obs_b) > 0:

        ratio = min(obs_a, obs_b) / max(obs_a, obs_b)

        if ratio > 0.5:
            score += 0.10

    return score


def recursive_convergence(events):

    merged = []
    consumed = set()

    for i, event in enumerate(events):

        if i in consumed:
            continue

        cluster = [event]

        for j, other in enumerate(events):

            if j <= i or j in consumed:
                continue

            similarity = recursive_similarity(
                event,
                other
            )

            # Recursive widening threshold.
            if similarity >= 0.60:

                cluster.append(other)
                consumed.add(j)

        if len(cluster) == 1:

            merged.append(event)
            continue

        merged.append(
            merge_recursive_cluster(cluster)
        )

    return merged


def merge_recursive_cluster(cluster):

    primary = max(
        cluster,
        key=lambda x: x.get("observation_count", 0)
    )

    merged_observations = sum(
        x.get("observation_count", 0)
        for x in cluster
    )

    merged_sources = set()

    for item in cluster:
        for source in item.get("sources", []):
            merged_sources.add(source)

    primary["observation_count"] = merged_observations

    primary["source_count"] = len(merged_sources)

    primary["sources"] = sorted(merged_sources)

    primary["evidence_summary"].append(
        f"Recursive convergence absorbed {len(cluster)-1} adjacent manifolds"
    )

    primary["manifold_topology"]["topology_class"] = (
        "Recursive Persistent Swarm Field"
    )

    return primary


# ============================================================
# BUILD PATCH
# ============================================================

# BEFORE:
# events.sort(...)

# INSERT:
events = recursive_convergence(events)

# THEN:
events.sort(...)
