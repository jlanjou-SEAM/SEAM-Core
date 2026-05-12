import json
from pathlib import Path
from datetime import datetime, UTC
from collections import defaultdict
ROOT=Path(__file__).resolve().parent; REPORTS=ROOT/'reports'; ANALYSIS=ROOT/'analysis'; REPORTS.mkdir(exist_ok=True); ANALYSIS.mkdir(exist_ok=True)
SIG={'seismic':'Lithic / Crustal Perturbation Field','space_weather':'Solar / Geomagnetic Gradient','ionospheric':'Ionospheric / RF Propagation Field','lightning':'Atmospheric Electrical Discharge','oceanic':'Oceanic Buoy / Hydrodynamic Telemetry','atmospheric':'Atmospheric State Vector','radiological':'Radiological / Environmental Sensor Field','unknown':'Unclassified SEAM Field'}
def now(): return datetime.now(UTC)
def load(name,key):
    p=REPORTS/name
    try: return json.loads(p.read_text(encoding='utf-8')).get(key,[])
    except Exception: return []
def lock(phi): return 'HARD LOCK' if phi>=.95 else 'TARGET' if phi>=.75 else 'FOLLOW' if phi>=.5 else 'MONITOR'
def tier(phi): return 'FULL DATA RECORDING' if phi>=.95 else 'TARGET ACQUISITION' if phi>=.75 else 'FOLLOW PROTOCOL' if phi>=.5 else 'IDLE/MONITOR'
def main():
    print('\n=== CLEAN-ROOM SEAM MASTER RECONCILIATION ===\n')
    mans=load('cross_stream_manifolds_current.json','manifolds'); tracks=load('persistent_field_tracks_current.json','tracks'); forecasts=load('forecast_cones_current.json','forecast_cones'); events=load('canonical_spacetime_events_current.json','canonical_events')
    matrix=defaultdict(lambda:{'payloads':0,'events':0,'max_phi':0,'regions':set()}); rows=[]
    for i,m in enumerate(mans):
        types=m.get('event_types') or ['unknown']; phi=float(m.get('seam_phi',0)); region=m.get('spatial_region') or 'NOLOC'; primary=types[0]
        for et in types:
            matrix[et]['payloads']+=int(m.get('density',0)); matrix[et]['events']+=int(m.get('event_count',0)); matrix[et]['max_phi']=max(matrix[et]['max_phi'],phi); matrix[et]['regions'].add(region)
        rows.append({'event_id':f'SEAM-{i:05d}-{primary.upper()}','acquisition_utc':now().isoformat(),'lock_state':lock(phi),'execution_tier':tier(phi),'phi':round(phi,4),'predicted_time_utc':'TBD','magnitude':m.get('density',0),'spatial_region':region,'lat_long':region,'course':'STATIC','signature':SIG.get(primary,'Unclassified SEAM Field'),'event_types':types,'manifold_id':m.get('manifold_id'),'event_count':m.get('event_count',0),'density':m.get('density',0)})
    sources=[]
    for r,d in sorted(matrix.items()):
        phi=d['max_phi']; sources.append({'regime':r,'lock_state':lock(phi),'execution_tier':tier(phi),'phi':round(phi,4),'payloads':d['payloads'],'events':d['events'],'region_count':len(d['regions']),'signature':SIG.get(r,'Unclassified SEAM Field')})
    out={'timestamp_utc':now().isoformat(),'schema':'SEAM Master Data Reconciliation v6.5.1','manifolds_input':len(mans),'tracks_input':len(tracks),'forecasts_input':len(forecasts),'events_input':len(events),'source_matrix':sources,'master_events':rows}
    (REPORTS/'seam_master_reconciliation_current.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    md=REPORTS/'seam_master_reconciliation_current.md'
    with open(md,'w',encoding='utf-8') as f:
        f.write('# SEAM Master Data Reconciliation [v6.5.1]\n\n'); f.write(f"Generated UTC: {out['timestamp_utc']}\n\n"); f.write('## Source Matrix\n\n| Regime | Lock State | Phi | Payloads | Events | Regions | Signature |\n|---|---:|---:|---:|---:|---:|---|\n')
        for s in sources: f.write(f"| {s['regime']} | {s['lock_state']} | {s['phi']} | {s['payloads']} | {s['events']} | {s['region_count']} | {s['signature']} |\n")
        f.write('\n## Active Manifest\n\n| Event ID | Acquisition UTC | Lock State | Pred. Time UTC | Magnitude | Lat/Long | Course | Signature |\n|---|---|---|---|---:|---|---|---|\n')
        for r in rows[:100]: f.write(f"| {r['event_id']} | {r['acquisition_utc']} | {r['lock_state']} ({r['phi']}) | {r['predicted_time_utc']} | {r['magnitude']} | {r['lat_long']} | {r['course']} | {r['signature']} |\n")
    with open(ANALYSIS/'seam_working_48h.jsonl','a',encoding='utf-8') as f: f.write(json.dumps(out)+'\n')
    print('Sources analyzed:',len(sources)); print('Master events:',len(rows)); print('Current JSON:',REPORTS/'seam_master_reconciliation_current.json'); print('Current MD:',md); print('\nSEAM master reconciliation complete.\n')
if __name__=='__main__': main()
