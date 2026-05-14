"""continuum_retention_manager.py v2.2-production
48h hot retention for raw/, decoded/, combined/. Curated is preserved for validation history.
"""
from pathlib import Path
from datetime import datetime, timezone
import shutil, re
ROOT=Path(__file__).resolve().parent
HOT_DIRS=[ROOT/'raw', ROOT/'decoded', ROOT/'combined']
ARCHIVE_ROOT=ROOT/'archive'
RETENTION_HOURS=48
VALID={'.json','.geojson','.jsonl','.txt','.csv','.xml','.payload'}
def now(): return datetime.now(timezone.utc)
def inferred_time(p):
    m=re.search(r'(20\d{2}-\d{2}-\d{2})',str(p))
    if m:
        try: return datetime.fromisoformat(m.group(1)).replace(tzinfo=timezone.utc)
        except Exception: pass
    return datetime.fromtimestamp(p.stat().st_mtime,tz=timezone.utc)
def age_hours(p): return (now()-inferred_time(p)).total_seconds()/3600
def main():
    moved=retained=0
    for d in HOT_DIRS:
        if not d.exists(): continue
        for p in d.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in VALID: continue
            if age_hours(p)<=RETENTION_HOURS:
                retained+=1; continue
            dest=ARCHIVE_ROOT/p.relative_to(ROOT)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.move(str(p),str(dest)); moved+=1
    print('\n=== SEAM RETENTION MANAGER v2.2-production ===\n')
    print(f'Retention window: {RETENTION_HOURS}h')
    print(f'Retained hot files: {retained}')
    print(f'Archived files: {moved}\n')
if __name__=='__main__': main()
