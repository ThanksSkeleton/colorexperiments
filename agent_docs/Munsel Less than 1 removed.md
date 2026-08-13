# Munsel Less than 1 removed

## Decision

This project uses Munsell Value `1` as the lower boundary of its practical
Munsell working domain. Munsell colors with Value below `1` are removed from
the published processed data and are not rendered or displayed by the Munsell
toys.

The project keeps its established `MUNSEL` experiment-name spelling, while
using the standard `Munsell` spelling for the color system in prose.

## Why

The current exploration uses OKLCH as its mathematical home, Munsell as an
artist-oriented color organization with practical compromises, and PCCS as an
artist-oriented categorization derived from Munsell coordinates.

Munsell Values `0.8`, `0.6`, `0.4`, and `0.2` belong to a specialized 1956
extension of the renotation system into very dark colors. They are not normal
Munsell Book working samples in the same sense as the ordinary Value range.
The extension deliberately produces extreme constant-Chroma geometry as Value
approaches theoretical black.

That behavior is useful historically, but it is not useful for the present
PCCS investigation. It introduces a strongly distorted tail into conversions
to OKLCH and into the PCCS saturation equation. Near black, the PCCS saturation
denominator approaches zero, which can force modest Munsell Chroma values far
outside the representative PCCS tone-center range. A nearest-center classifier
then gives labels such as Vivid to colors that are not meaningfully close to a
normal Vivid region.

Removing the sub-1 extension does not solve the entire PCCS Vivid issue. Some
purple samples at Value `1` and above may still receive implausible Vivid
labels. It does, however, remove a special theoretical region whose geometry
dominates the diagnostic and leaves a smaller, more practically relevant
classification problem.

## Implementation policy

- `scripts/munsell_dat_to_oklch_csv.py` discards source rows below Value `1`
  before midpoint interpolation or neutral-axis generation.
- `scripts/classify_munsell_pccs.py` will not emit PCCS classifications below
  Value `1`, even when given a broader input CSV.
- Published Munsell and PCCS CSV assets contain no rows below Value `1`.
- Every browser toy that consumes the assets also filters out rows below Value
  `1` as a defensive boundary.
- The standalone Munsell Value contour toy draws and reports Munsell Value only
  from `V1` upward. Its underlying OKLCH plane remains visible below that
  boundary because the plane is not itself Munsell data.
- Tonal palette logic no longer treats Values `0.2–0.9` as a special Dark
  Region. Its black/off-black choice is the darkest remaining eligible sample.

This is a scoped project decision, not a claim that sub-1 Munsell renotation
coordinates are invalid or that the 1956 extension should be erased from the
historical description of the system.
