"""
seam_unified_48h_field.py
Version: 2.2-production

Build combined/ from raw/ + decoded/ only.
Does not read curated/, combined/, analysis/, data/, logs/, or archive/.
"""
from __future__ import annotations
import json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent
INPUT_DIRS = [("raw", ROOT / "raw"), ("decoded", ROOT / "decoded")]
COMBINED_DIR = ROOT / "combined"
OUTPUT = COMBINED_DIR / "seam_unified_recursive_field_48h.json"
OUTPUT_JSONL = COMBINED_DIR / "seam_unified_recursive_field_48h.jsonl"
RETENTION_HOURS = 48
MAX_FILE_BYTES = 5_000_000
VALID_SUFFIXES = {".json", ".geojson"}

def now_utc(): return datetime.now(timezone.utc)

def parse_time(v: Any) -> Optional[datetime]:
    if v is None: return None
    if isinstance(v,(int,float)):
        try:
            return datetime.fromtimestamp(v/1000 if v>10_000_000_000 else v, tz=timezone.utc)
        except Exception: return None
    s=str(v).strip()
    if not s: return None
    try:
        d=datetime.fromisoformat(s.replace('Z','+00:00'))
        return (d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc))
    except Exception: pass
    if s.isdigit():
        try:
            n=int(s); return datetime.fromtimestamp(n/1000 if n>10_000_000_000 else n, tz=timezone.utc)
        except Exception: return None
    return None

def best_time(obj: Any, path: Path) -> Optional[datetime]:
    vals=[]
    def scan(x):
        if isinstance(x,dict):
            for k in ['time','updated','timestamp','timestamp_utc','datetime','date','created_utc','first_seen_utc','last_seen_utc','generated_utc']:
                if k in x: vals.append(x.get(k))
            if isinstance(x.get('properties'),dict): scan(x['properties'])
    scan(obj)
    for v in vals:
        d=parse_time(v)
        if d: return d
    m=re.search(r'(20\d{2}-\d{2}-\d{2})', str(path))
    if m:
        try: return datetime.fromisoformat(m.group(1)).replace(tzinfo=timezone.utc)
        except Exception: pass
    try: return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except Exception: return None

def load_json(path: Path):
    if path.stat().st_size > MAX_FILE_BYTES: return None
    try: return json.loads(path.read_text(encoding='utf-8', errors='replace'))
    except Exception: return None

def iter_obs(payload):
    if isinstance(payload,dict):
        if payload.get('type')=='FeatureCollection' and isinstance(payload.get('features'),list):
            yield from payload['features']; return
        if payload.get('type')=='Feature': yield payload; return
        for k in ['events','features','records','items','data','results']:
            if isinstance(payload.get(k),list):
                yield from payload[k]; return
        yield payload; return
    if isinstance(payload,list): yield from payload

def coords(obs):
    if not isinstance(obs,dict): return None,None
    g=obs.get('geometry')
    if isinstance(g,dict) and isinstance(g.get('coordinates'),list) and len(g['coordinates'])>=2:
        try: return float(g['coordinates'][1]), float(g['coordinates'][0])
        except Exception: pass
    p=obs.get('properties') if isinstance(obs.get('properties'),dict) else obs
    for la in ['lat','latitude']:
        for lo in ['lon','lng','longitude']:
            if la in p and lo in p:
                try: return float(p[la]), float(p[lo])
                except Exception: pass
    return None,None

def regime(obs,path):
    t=(str(path)+' '+json.dumps(obs,default=str)[:2000]).lower()
    if any(x in t for x in ['earthquake','seismic','quake','"mag"']): return 'seismic'
    if any(x in t for x in ['solar','swpc','goes','xray','geomagnetic','kp']): return 'space_weather'
    if any(x in t for x in ['lightning','blitz','storm']): return 'atmospheric_electric'
    if any(x in t for x in ['radio','seti','lofar','sdr','beacon','madrigal','ionosphere']): return 'radio_ionospheric'
    if any(x in t for x in ['buoy','ocean','argo','wave']): return 'marine'
    if any(x in t for x in ['radiation','safecast']): return 'radiological'
    return 'unknown'

def compact(obs):
    try:
        s=json.dumps(obs,ensure_ascii=False,default=str)
        return obs if len(s)<=6000 else {'payload_excerpt':s[:6000]}
    except Exception: return str(obs)[:6000]

def main():
    print('\n=== SEAM UNIFIED FIELD v2.2-production ===\n')
    cutoff=now_utc()-timedelta(hours=RETENTION_HOURS)
    observations=[]; files_seen=0; files_used=0
    for layer, base in INPUT_DIRS:
        if not base.exists(): continue
        for path in base.rglob('*'):
            if not path.is_file() or path.suffix.lower() not in VALID_SUFFIXES: continue
            files_seen+=1
            payload=load_json(path)
            if payload is None: continue
            used=False
            ptime=best_time(payload,path)
            if ptime and ptime < cutoff: continue
            for ob in iter_obs(payload):
                ts=best_time(ob,path) or ptime
                if not ts or ts < cutoff: continue
                lat,lon=coords(ob)
                observations.append({'observation_id':f'OBS-{len(observations):08d}','timestamp_utc':ts.isoformat(),'ingested_utc':now_utc().isoformat(),'epistemic_layer':layer,'source':path.relative_to(base).parts[0] if len(path.relative_to(base).parts)>1 else 'unknown','source_file':str(path.relative_to(ROOT)),'regime':regime(ob,path),'latitude':lat,'longitude':lon,'has_spatial':lat is not None and lon is not None,'payload':compact(ob)})
                used=True
            if used: files_used+=1
    counts={}; layers={}; spatial=0
    for o in observations:
        counts[o['regime']]=counts.get(o['regime'],0)+1
        layers[o['epistemic_layer']]=layers.get(o['epistemic_layer'],0)+1
        spatial += 1 if o['has_spatial'] else 0
    field={'schema':'SEAM_UNIFIED_RECURSIVE_FIELD','version':'2.2-production','generated_utc':now_utc().isoformat(),'retention_hours':RETENTION_HOURS,'cutoff_utc':cutoff.isoformat(),'inputs':['raw','decoded'],'excluded_inputs':['curated','combined','analysis','data','logs','archive'],'files_seen':files_seen,'files_used':files_used,'observation_count':len(observations),'spatial_observation_count':spatial,'regime_counts':counts,'epistemic_layer_counts':layers,'observations':observations}
    COMBINED_DIR.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(field,indent=2,ensure_ascii=False),encoding='utf-8')
    with OUTPUT_JSONL.open('w',encoding='utf-8') as f:
        for o in observations: f.write(json.dumps(o,ensure_ascii=False,default=str)+'\n')
    print(f"Files seen: {files_seen}")
    print(f"Files used: {files_used}")
    print(f"Observations: {len(observations)}")
    print(f"Spatial observations: {spatial}")
    print(f"Regimes: {counts}")
    print(f"Layers: {layers}")
    print(f"Output: {OUTPUT}\n")
if __name__=='__main__': main()
