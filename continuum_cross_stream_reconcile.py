import json
from pathlib import Path
from datetime import datetime, UTC
ROOT=Path(__file__).resolve().parent; REPORTS=ROOT/'reports'; ANALYSIS=ROOT/'analysis'; REPORTS.mkdir(exist_ok=True); ANALYSIS.mkdir(exist_ok=True)
def now(): return datetime.now(UTC)
def lock(phi): return 'HARD LOCK' if phi>=.95 else 'TARGET' if phi>=.75 else 'FOLLOW' if phi>=.5 else 'MONITOR'
def label(types):
    s=set(types or [])
    if {'seismic','ionospheric','space_weather'}.issubset(s): return 'SEAM_COUPLED_LITHOSPHERIC_EM_FIELD'
    if 'seismic' in s: return 'SEAM_LITHIC_PERTURBATION'
    if 'space_weather' in s: return 'SEAM_HELIOSPHERIC_FORCING'
    if 'ionospheric' in s: return 'SEAM_ELECTROMAGNETIC_COHERENCE'
    if 'lightning' in s: return 'SEAM_ATMOSPHERIC_DISCHARGE'
    if 'oceanic' in s: return 'SEAM_HYDRODYNAMIC_RESPONSE'
    if 'atmospheric' in s: return 'SEAM_ATMOSPHERIC_STATE_VECTOR'
    if 'radiological' in s: return 'SEAM_ENVIRONMENTAL_RADIATION_FIELD'
    return 'SEAM_UNRESOLVED_FIELD'
def main():
    print('\n=== CLEAN-ROOM EVENT-BUS MANIFOLD RECONCILIATION ===\n')
    p=REPORTS/'spatial_aggregate_current.json'; data=json.loads(p.read_text()) if p.exists() else {'aggregates':[]}
    mans=[]
    for i,a in enumerate(data.get('aggregates',[])):
        phi=float(a.get('seam_phi',0)); types=a.get('event_types',[])
        mans.append({'manifold_id':f'MANI-{i:05d}','timestamp_utc':now().isoformat(),'event_label':label(types),'event_types':types,'lock_state':lock(phi),'seam_phi':round(phi,4),'density':a.get('density',0),'event_count':a.get('event_count',0),'spatial_region':a.get('spatial_region'),'aggregate_id':a.get('aggregate_id')})
    out={'timestamp_utc':now().isoformat(),'aggregate_input_count':len(data.get('aggregates',[])),'manifold_count':len(mans),'manifolds':mans}
    (REPORTS/'cross_stream_manifolds_current.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    with open(ANALYSIS/'cross_stream_working_48h.jsonl','a',encoding='utf-8') as f:
        for m in mans: f.write(json.dumps(m)+'\n')
    print('Spatial aggregates:',out['aggregate_input_count']); print('Manifolds:',len(mans)); print('Current:',REPORTS/'cross_stream_manifolds_current.json'); print('\nEvent-bus manifold reconciliation complete.\n')
if __name__=='__main__': main()
