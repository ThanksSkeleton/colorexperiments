# Historical Activity: Initial Asset Repair

The corrected prototype originally expected a global mask-asset object that was not defined. The paper-doll layers therefore failed to render.

The prototype was changed to reference local assets directly:

- `female_layers/{role}.png`
- `male_layers/{role}.png`
- `starburst.svg`

Rendering code then read from those local paths. This established the standalone asset layout used by later iterations.
