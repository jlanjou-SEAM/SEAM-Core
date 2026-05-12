import json, math
from pathlib import Path
from datetime import datetime, UTC
ROOT=Path(__file__).resolve().parent; REPORTS=ROOT/'reports'; ANALYSIS=ROOT/'analysis'; REPORTS.mkdir(exist_ok=True); ANALYSIS.mkdir(exist_ok=True)
WIN=600; RADIUS=10.0
def now(): return datetime.now(UTC)
def parse(x):
    try: return datetime.fromisoformat(x.replace('Z','+00:00'))
    except Exception: return now()
def dist(a,b,c,d): return math.hypot((c-a)*69,(d-b)*69*math.cos(math.radians((a+c)/2)))
def main():
    print('\n=== CLEAN-ROOM PERSISTENT FIELD TRACKING ===\n')
    p=REPORTS/'canonical_spacetime_events_current.json'; events=json.loads(p.read_text()).get('canonical_events',[]) if p.exists() else []
    tracks=[]
    for e in sorted(events,key=lambda x:x.get('first_seen_utc','')):
        lat=e.get('latitude'); lon=e.get('longitude'); ts=parse(e.get('last_seen_utc',''))
        if lat is None or lon is None: continue
        found=None
        for t in tracks:
            if t['primary_regime']!=e.get('primary_regime'): continue
            if abs((ts-parse(t['last_seen_utc'])).total_seconds())<=WIN and dist(lat,lon,t['current_latitude'],t['current_longitude'])<=RADIUS: found=t; break
        if found:
            dl=lat-found['current_latitude']; dn=lon-found['current_longitude']; found['current_latitude']=lat; found['current_longitude']=lon; found['last_seen_utc']=ts.isoformat(); found['event_count']+=1; found['velocity_vector']={'delta_latitude':round(dl,6),'delta_longitude':round(dn,6)}; found['forecast_position']={'latitude':round(lat+dl,6),'longitude':round(lon+dn,6)}; found['trajectory'].append({'timestamp':ts.isoformat(),'latitude':lat,'longitude':lon})
        else:
            tracks.append({'persistent_track_id':f'TRACK-{len(tracks):05d}','primary_regime':e.get('primary_regime','unknown'),'first_seen_utc':ts.isoformat(),'last_seen_utc':ts.isoformat(),'current_latitude':lat,'current_longitude':lon,'event_count':1,'velocity_vector':{'delta_latitude':0.0,'delta_longitude':0.0},'forecast_position':{'latitude':lat,'longitude':lon},'trajectory':[{'timestamp':ts.isoformat(),'latitude':lat,'longitude':lon}]})
    out={'timestamp_utc':now().isoformat(),'track_count':len(tracks),'tracks':tracks}
    (REPORTS/'persistent_field_tracks_current.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    with open(ANALYSIS/'persistent_field_tracks_48h.jsonl','a',encoding='utf-8') as f:
        for t in tracks: f.write(json.dumps(t)+'\n')
    print('Persistent tracks:',len(tracks)); print('Current:',REPORTS/'persistent_field_tracks_current.json'); print('\nPersistent field tracking complete.\n')
if __name__=='__main__': main()
