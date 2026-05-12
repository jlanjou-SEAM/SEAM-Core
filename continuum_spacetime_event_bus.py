import json, math
from pathlib import Path
from datetime import datetime, UTC
from collections import defaultdict
ROOT=Path(__file__).resolve().parent
DECODED=ROOT/'decoded'; REPORTS=ROOT/'reports'; ANALYSIS=ROOT/'analysis'
REPORTS.mkdir(exist_ok=True); ANALYSIS.mkdir(exist_ok=True)
IN=DECODED/'decoded_payloads.jsonl'
WINDOW_SECONDS=10; WINDOW_MILES=0.25; GRID_PRECISION=3
SOURCE_MAP={'USGS':'seismic','EMSC':'seismic','IRIS':'seismic','RaspberryShake':'seismic','NOAA_SWPC':'space_weather','GOES':'space_weather','StanfordSID':'ionospheric','KiwiSDR':'ionospheric','WebSDR':'ionospheric','ReverseBeaconNetwork':'ionospheric','Blitzortung':'lightning','LightningMaps':'lightning','NOAA_Buoys':'oceanic','ARGO':'oceanic','Safecast':'radiological','MADIS':'atmospheric','CWOP':'atmospheric','USCRN':'atmospheric','OpenSky':'atmospheric'}
def now(): return datetime.now(UTC)
def parse(t):
    try:
        if isinstance(t,str): return datetime.fromisoformat(t.replace('Z','+00:00'))
    except Exception: pass
    return now()
def regime(row):
    s=(row.get('source') or row.get('source_file') or '').lower()
    for k,v in SOURCE_MAP.items():
        if k.lower() in s: return v
    return 'unknown'
def bucket(lat,lon): return f'{round(lat,GRID_PRECISION)}_{round(lon,GRID_PRECISION)}'
def neighbors(lat,lon):
    lat=round(lat,GRID_PRECISION); lon=round(lon,GRID_PRECISION); step=10**-GRID_PRECISION
    return [f'{round(lat+a,GRID_PRECISION)}_{round(lon+b,GRID_PRECISION)}' for a in (-step,0,step) for b in (-step,0,step)]
def dist(lat1,lon1,lat2,lon2):
    return math.hypot((lat2-lat1)*69.0,(lon2-lon1)*69.0*math.cos(math.radians((lat1+lat2)/2)))
def lock(phi): return 'HARD LOCK' if phi>=.95 else 'TARGET' if phi>=.75 else 'FOLLOW' if phi>=.5 else 'MONITOR'
def main():
    print('\n=== CLEAN-ROOM HIGH-SPEED SPACE-TIME EVENT BUS ===\n')
    events=[]; idx=defaultdict(list); processed=spatial=matched=created=0
    if not IN.exists(): IN.write_text('', encoding='utf-8')
    with open(IN,'r',encoding='utf-8') as f:
        for line in f:
            processed+=1
            try: row=json.loads(line)
            except Exception: continue
            lat=row.get('latitude'); lon=row.get('longitude')
            if lat is None or lon is None: continue
            try: lat=float(lat); lon=float(lon)
            except Exception: continue
            spatial+=1; rg=regime(row); ts=parse(row.get('decoded_timestamp_utc')); found=None
            for k in neighbors(lat,lon):
                for ei in idx.get((rg,k),[]):
                    e=events[ei]
                    if abs((ts-e['_dt']).total_seconds())>WINDOW_SECONDS: continue
                    if dist(lat,lon,e['latitude'],e['longitude'])<=WINDOW_MILES: found=e; break
                if found: break
            if found:
                found['observation_count']+=1; found['last_seen_utc']=ts.isoformat(); found['_dt']=ts; found['source_set'].add(row.get('source_file','')); found['source_count']=len(found['source_set']); found['seam_phi']=min(.999, found['observation_count']/25); found['lock_state']=lock(found['seam_phi']); matched+=1
            else:
                e={'canonical_event_id':f'EVT-{len(events):06d}','created_utc':now().isoformat(),'first_seen_utc':ts.isoformat(),'last_seen_utc':ts.isoformat(),'_dt':ts,'primary_regime':rg,'latitude':lat,'longitude':lon,'observation_count':1,'source_count':1,'source_set':{row.get('source_file','')},'seam_phi':0.04,'lock_state':'MONITOR'}
                events.append(e); idx[(rg,bucket(lat,lon))].append(len(events)-1); created+=1
    clean=[]
    for e in events:
        d=dict(e); d.pop('_dt',None); d['sources']=sorted(d.pop('source_set',set())); clean.append(d)
    out={'timestamp_utc':now().isoformat(),'records_processed':processed,'spatial_records':spatial,'matched_observations':matched,'created_events':created,'canonical_event_count':len(clean),'canonical_events':clean}
    (REPORTS/'canonical_spacetime_events_current.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    with open(ANALYSIS/'canonical_spacetime_working_48h.jsonl','a',encoding='utf-8') as f:
        for e in clean: f.write(json.dumps(e)+'\n')
    print('Records processed:',processed); print('Spatial records:',spatial); print('Created events:',created); print('Matched observations:',matched); print('Canonical events:',len(clean)); print('Current:', REPORTS/'canonical_spacetime_events_current.json'); print('\nHigh-speed event bus complete.\n')
if __name__=='__main__': main()
