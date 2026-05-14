"""
continuum_retention_manager.py
Version: 2.0

Retention Architecture:
-----------------------
raw/      -> 48h hot
decoded/  -> 48h hot
combined/ -> 48h hot

curated/  -> preserved longer-term
archive/  -> cold storage

Purpose:
--------
Prevent recursive contamination and storage explosion.
"""

from pathlib import Path
from datetime import datetime, timezone, timedelta
import shutil

ROOT = Path(__file__).resolve().parent

HOT_DIRS = [
    ROOT / "raw",
    ROOT / "decoded",
    ROOT / "combined"
]

ARCHIVE_ROOT = ROOT / "archive"

RETENTION_HOURS = 48


def utc_now():
    return datetime.now(timezone.utc)


def age_hours(path: Path):

    modified = datetime.fromtimestamp(
        path.stat().st_mtime,
        tz=timezone.utc
    )

    return (
        utc_now() - modified
    ).total_seconds() / 3600


def archive_destination(path: Path):

    return ARCHIVE_ROOT / path.relative_to(ROOT)


def process():

    moved = 0

    for root in HOT_DIRS:

        if not root.exists():
            continue

        for path in root.rglob("*"):

            if not path.is_file():
                continue

            if age_hours(path) <= RETENTION_HOURS:
                continue

            destination = archive_destination(path)

            destination.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            shutil.move(
                str(path),
                str(destination)
            )

            moved += 1

    return moved


def main():

    print()
    print("=== SEAM RETENTION MANAGER v2.0 ===")
    print()

    moved = process()

    print(f"Retention window: {RETENTION_HOURS}h")
    print(f"Archived files : {moved}")
    print()


if __name__ == "__main__":
    main()
