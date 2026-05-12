import json
from pathlib import Path
from datetime import datetime, UTC
from collections import defaultdict
ROOT=Path(__file__).resolve().parent; REPORTS=ROOT/'reports'; ANALYSIS=ROOT/'analysis'; REPORTS.mkdir(exist_ok=True); ANALYSIS.mkdir(exist_ok=True)
def now(): return datetime.now(UTC)
def main():
    print('\n=== CLEAN-ROOM REINFORCEMENT AGGREGATE ===\n')
    p=REPORTS/'canonical_spacetime_events_current.json'
    data=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'canonical_events':[]}
    groups=defaultdict(list)
    for e in data.get('canonical_events',[]): groups[f"{round(float(e['latitude']),1)}_{round(float(e['longitude']),1)}"].append(e)
    aggs=[]
    for i,(region,rows) in enumerate(groups.items()):
        phi=max(float(x.get('seam_phi',0)) for x in rows); density=sum(int(x.get('observation_count',0)) for x in rows); types=sorted(set(x.get('primary_regime','unknown') for x in rows))
        aggs.append({'aggregate_id':f'AGG-{i:05d}','timestamp_utc':now().isoformat(),'spatial_region':region,'event_types':types,'density':density,'event_count':len(rows),'reinforcement_acceleration':round(density/max(len(rows),1),4),'seam_phi':round(phi,4)})
    out={'timestamp_utc':now().isoformat(),'aggregate_count':len(aggs),'aggregates':aggs}
    (REPORTS/'spatial_aggregate_current.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    with open(ANALYSIS/'spatial_aggregate_working_48h.jsonl','a',encoding='utf-8') as f:
        for a in aggs: f.write(json.dumps(a)+'\n')
    print('Aggregates:',len(aggs)); print('Current:',REPORTS/'spatial_aggregate_current.json'); print('\n')
if __name__=='__main__': main()
