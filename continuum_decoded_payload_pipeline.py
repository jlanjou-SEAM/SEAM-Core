import json, hashlib
from pathlib import Path
from datetime import datetime, UTC

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw'; CURATED=ROOT/'curated'; DECODED=ROOT/'decoded'; STATE=ROOT/'state'
for p in [DECODED, STATE]: p.mkdir(exist_ok=True)
STATE_FILE=STATE/'decoded_processed_index.json'
OUT=DECODED/'decoded_payloads.jsonl'
SUPPORTED={'.json','.geojson'}

def now(): return datetime.now(UTC).isoformat()
def sha1(path):
    h=hashlib.sha1()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(65536), b''): h.update(b)
    return h.hexdigest()
def load_state():
    try: return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except Exception: return {}
def save_state(s): STATE_FILE.write_text(json.dumps(s, indent=2), encoding='utf-8')

def source_from_path(p):
    parts=p.parts
    for root in ('raw','curated'):
        if root in parts:
            i=parts.index(root)
            if i+1 < len(parts): return parts[i+1]
    return 'unknown'

def walk_records(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get('features'), list):
            for x in obj['features']: yield x
        elif 'payload' in obj:
            yield from walk_records(obj['payload'])
        elif isinstance(obj.get('data'), list):
            for x in obj['data']: yield x
        else:
            yield obj
    elif isinstance(obj, list):
        for x in obj: yield from walk_records(x)

def find_coord(row):
    lat=lon=None
    if not isinstance(row, dict): return None,None
    try:
        coords=row.get('geometry',{}).get('coordinates')
        if isinstance(coords, list) and len(coords)>=2:
            lon=float(coords[0]); lat=float(coords[1]); return lat,lon
    except Exception: pass
    keys_lat=['lat','latitude','Latitude','LAT']
    keys_lon=['lon','lng','longitude','Longitude','LON']
    for lk in keys_lat:
        if lk in row:
            for ok in keys_lon:
                if ok in row:
                    try: return float(row[lk]), float(row[ok])
                    except Exception: pass
    props=row.get('properties') if isinstance(row.get('properties'),dict) else {}
    for lk in keys_lat:
        if lk in props:
            for ok in keys_lon:
                if ok in props:
                    try: return float(props[lk]), float(props[ok])
                    except Exception: pass
    return None,None

def row_time(row):
    if not isinstance(row, dict): return now()
    props=row.get('properties') if isinstance(row.get('properties'),dict) else {}
    for d in (row, props):
        for k in ('time','timestamp','timestamp_utc','date','datetime'):
            v=d.get(k)
            if v is None: continue
            if isinstance(v,(int,float)):
                # USGS ms
                try:
                    from datetime import datetime, UTC
                    if v > 10_000_000_000: v=v/1000
                    return datetime.fromtimestamp(v, UTC).isoformat()
                except Exception: pass
            if isinstance(v,str): return v
    return now()

def process(path):
    try: data=json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    except Exception: return []
    source=source_from_path(path)
    out=[]
    for rec in walk_records(data):
        if not isinstance(rec, dict): continue
        lat,lon=find_coord(rec)
        out.append({'decoded_timestamp_utc': row_time(rec), 'ingested_utc': now(), 'source_file': str(path), 'source': source, 'latitude': lat, 'longitude': lon, 'payload': rec})
    return out

def main():
    print('\n=== CLEAN-ROOM INCREMENTAL PAYLOAD PIPELINE ===\n')
    state=load_state(); processed=skipped=decoded=0
    files=[]
    for root in (RAW, CURATED):
        if root.exists():
            for ext in SUPPORTED: files.extend(root.rglob(f'*{ext}'))
    with open(OUT,'a',encoding='utf-8') as f:
        for path in sorted(files):
            try: digest=sha1(path)
            except Exception: continue
            key=str(path)
            if state.get(key)==digest:
                skipped += 1; continue
            rows=process(path)
            for r in rows:
                f.write(json.dumps(r,separators=(',',':'))+'\n'); decoded += 1
            state[key]=digest; processed += 1
    save_state(state)
    print('Processed files:', processed)
    print('Skipped unchanged:', skipped)
    print('Decoded rows:', decoded)
    print('Decoded output:', OUT)
    print('State index:', STATE_FILE)
    print('\nIncremental processing complete.\n')
if __name__=='__main__': main()
