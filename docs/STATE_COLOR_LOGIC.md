# State and Hazard Color Logic

SEAM uses hazard-oriented color logic.

This means high likelihood is danger-colored, not success-colored.

| State | Visual Meaning |
|---|---|
| TARGET | locked/high-priority target, red |
| FOLLOW | active follow state, amber |
| MONITOR | lower-priority monitoring, slate |

## Target Rendering

TARGET should render with:

- deep red card border
- red header emphasis
- red state text
- red lock badge
- red/orange likelihood heat

## Probability Heat

| Likelihood | Color |
|---|---|
| >= 70% | red |
| >= 55% | orange |
| >= 35% | yellow/amber |
| < 35% | neutral slate |

The goal is countdown-to-disaster semantics, not green success semantics.
