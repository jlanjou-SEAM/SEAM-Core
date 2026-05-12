# SEAM Startup Semantics

## Correct behavior

Startup must finish.

It should not enter an infinite loop unless explicitly launched in runtime mode.

## Modes

### Finite bootstrap mode

Runs once.

Purpose:

- verify Python environment
- verify collector imports
- test source requests
- write logs/bootstrap_report.json
- start UI server

### Continuous runtime mode

Runs until stopped.

Purpose:

- repeated collector cycles
- long-term accumulation
- operational monitoring

This is launched only by `runtime.bat` or `runtime.sh`.
