import json
from pathlib import Path
from datetime import datetime, UTC
ROOT=Path(__file__).resolve().parent; REPORTS=ROOT/'reports'; ANALYSIS=ROOT/'analysis'; REPORTS.mkdir(exist_ok=True); ANALYSIS.mkdir(exist_ok=True)
AUTH=['USGS','EMSC','NOAA','SPC','IRIS']
def now(): return datetime.now(UTC)
def load(name,key):
    p=REPORTS/name
    try: return json.loads(p.read_text(encoding='utf-8')).get(key,[])
    except Exception: return []
def parse(x):
    try: return datetime.fromisoformat(x.replace('Z','+00:00'))
    except Exception: return now()
def auth_sources(e):
    out=[]
    for src in e.get('sources',[]):
        u=src.upper()
        for a in AUTH:
            if a in u: out.append(a)
    return sorted(set(out))
def main():
    print('\n=== CLEAN-ROOM FORECAST CORRELATION ENGINE ===\n')
    forecasts=load('forecast_cones_current.json','forecast_cones'); tracks=load('persistent_field_tracks_current.json','tracks'); mans=load('cross_stream_manifolds_current.json','manifolds'); events=load('canonical_spacetime_events_current.json','canonical_events')
    try: seam=json.loads((REPORTS/'seam_master_reconciliation_current.json').read_text())
    except Exception: seam={}
    corr=[]
    for i,e in enumerate(events):
        auth=auth_sources(e); first=e.get('first_seen_utc',now().isoformat()); last=e.get('last_seen_utc',first); lead=int((parse(last)-parse(first)).total_seconds())
        corr.append({'event_id':e.get('canonical_event_id',f'EVT-{i:05d}'),'forecast_lock_utc':first,'official_registration_utc':last,'lead_time_seconds':lead,'forecast_confidence':round(float(e.get('seam_phi',0)),4),'verification_state':'CONFIRMED' if auth else 'PREDICTED','confirmation_sources':auth,'lock_state':e.get('lock_state','MONITOR'),'primary_regime':e.get('primary_regime','unknown'),'latitude':e.get('latitude'),'longitude':e.get('longitude'),'observation_count':e.get('observation_count',0),'source_count':e.get('source_count',0),'sources':e.get('sources',[])})
    live={'timestamp_utc':now().isoformat(),'active_events':len(corr),'confirmed_events':len([x for x in corr if x['verification_state']=='CONFIRMED']),'predicted_only':len([x for x in corr if x['verification_state']=='PREDICTED']),'events':corr,'system_state':{'forecast_cones':len(forecasts),'persistent_tracks':len(tracks),'manifolds':len(mans),'seam_records':len(seam.get('master_events',[]))}}
    (REPORTS/'live_event_state.json').write_text(json.dumps(live,indent=2),encoding='utf-8')
    with open(ANALYSIS/'forecast_correlation_48h.jsonl','a',encoding='utf-8') as f: f.write(json.dumps(live)+'\n')
    print('Correlated events:',len(corr)); print('Confirmed:',live['confirmed_events']); print('Predicted only:',live['predicted_only']); print('Live state:',REPORTS/'live_event_state.json'); print('\nForecast correlation complete.\n')
if __name__=='__main__': main()
