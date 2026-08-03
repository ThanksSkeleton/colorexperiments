# Historical Activity: Doll Rendering Improvements

## Integrated power layers

The separate power-symbol slots were removed. `power` became a normal paper-doll layer alongside:

```text
skin, main, support, accent, hair, eyes, power
```

Each doll received a same-canvas `power.png` mask. The masks use filled starbursts positioned at the outward hands, with a glow applied to the power layer.

## Doll carousel

The display was changed to show one doll type at a time:

- Male appears first.
- Female appears second.
- Previous and Next controls cycle through the available doll definitions.

The doll catalog and rendering functions were structured so additional doll definitions could be added later.

## School-uniform treatment

A school-uniform treatment was added as an alternative costume assignment:

- Primary: `#dadae1`
- Secondary: `#008080`
- Highlight: `#e50000`

Hair, eyes, and power remain derived from the active palette. Skin continues to use its separately configured color.
