import time, subprocess
from pathlib import Path
from datetime import datetime, UTC, timedelta
ROOT=Path(__file__).resolve().parent; RAW=ROOT/'raw'; DECODED=ROOT/'decoded'
RAW_RETENTION_MINUTES=60; DECODED_RETENTION_MINUTES=60; POLL_SECONDS=10
PIPELINE=[('continuum_dual_acquisition_runtime.py','--single-pass'),('continuum_decoded_payload_pipeline.py',None),('continuum_spacetime_event_bus.py',None),('continuum_spatial_aggregate.py',None),('continuum_cross_stream_reconcile.py',None),('continuum_persistent_field_tracking.py',None),('continuum_forecast_cone_engine.py',None),('continuum_stage2_seam_reconcile.py',None),('continuum_forecast_correlation_engine.py',None)]
def now(): return datetime.now(UTC)
def purge(root,mins):
    cutoff=now()-timedelta(minutes=mins); n=0
    if not root.exists(): return 0
    for f in root.rglob('*'):
        if not f.is_file() or 'current' in f.name.lower(): continue
        try:
            if datetime.fromtimestamp(f.stat().st_mtime,UTC)<cutoff: f.unlink(missing_ok=True); n+=1
        except Exception: pass
    return n
def run(script,arg=None):
    p=ROOT/script
    if not p.exists(): print('[MISSING]',script); return False
    cmd=['python',str(p)] + ([arg] if arg else [])
    print('\n'+'='*90); print('RUNNING:',script); print('='*90+'\n')
    s=time.time(); r=subprocess.run(cmd,cwd=str(ROOT)); print('\n[COMPLETE]',script,'|',round(time.time()-s,2),'s'); return r.returncode==0
print('\n=== CLEAN-ROOM UNIFIED REALTIME SEAM RUNTIME ===\n')
cycle=0
while True:
    cycle+=1; start=time.time(); print('\n'+'='*90); print(f'CYCLE {cycle} | {now().isoformat()}'); print('='*90)
    print(f'[INPUT STATE] raw_files={len(list(RAW.rglob("*.*"))) if RAW.exists() else 0} decoded_files={len(list(DECODED.rglob("*.*"))) if DECODED.exists() else 0}')
    for script,arg in PIPELINE: run(script,arg)
    print(f'[PURGE] raw={purge(RAW,RAW_RETENTION_MINUTES)} decoded={purge(DECODED,DECODED_RETENTION_MINUTES)}')
    elapsed=round(time.time()-start,2); sleep=max(0,POLL_SECONDS-elapsed)
    print('-'*90); print('Cycle runtime:',elapsed,'s'); print('Sleep:',sleep,'s'); print('-'*90); time.sleep(sleep)
