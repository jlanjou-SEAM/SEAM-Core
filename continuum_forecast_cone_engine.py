import json
from pathlib import Path
from datetime import datetime, UTC
ROOT=Path(__file__).resolve().parent; REPORTS=ROOT/'reports'; REPORTS.mkdir(exist_ok=True)
def now(): return datetime.now(UTC)
def main():
    print('\n=== CLEAN-ROOM FORECAST CONE ENGINE ===\n')
    p=REPORTS/'persistent_field_tracks_current.json'; tracks=json.loads(p.read_text()).get('tracks',[]) if p.exists() else []
    cones=[]
    for i,t in enumerate(tracks):
        v=t.get('velocity_vector',{}); rad=round((abs(v.get('delta_latitude',0))+abs(v.get('delta_longitude',0))+.01)*100,3)
        cones.append({'cone_id':f'CONE-{i:05d}','track_id':t.get('persistent_track_id'), 'forecast_center':t.get('forecast_position'), 'confidence_radius_miles':rad, 'event_count':t.get('event_count',0)})
    out={'timestamp_utc':now().isoformat(),'forecast_cone_count':len(cones),'forecast_cones':cones}
    (REPORTS/'forecast_cones_current.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print('Forecast cones:',len(cones)); print('Current:',REPORTS/'forecast_cones_current.json'); print('\n')
if __name__=='__main__': main()
