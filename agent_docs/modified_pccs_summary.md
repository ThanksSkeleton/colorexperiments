# Modified PCCS Summary

## Purpose

Modified PCCS is an exploratory extension of the project’s experimental PCCS
tone classifier. It addresses implausible classifications in the dark part of
the color space, especially cases where an unbounded nearest-center region
assigns Vivid or another light-associated tone to a very dark color.

It is not presented as an authoritative correction to PCCS. It is a practical
guardrail intended to produce more aesthetically coherent classifications for
this project while preserving ordinary PCCS behavior elsewhere.

## Starting problem

The existing classifier converts a color to PCCS saturation and tone-relative
lightness, then assigns the nearest of 14 representative PCCS tone centers in
the two-dimensional `(s, t)` plane.

Ordinary Euclidean Voronoi regions are unbounded. A tone therefore continues to
own coordinates far beyond the area where its label remains intuitively
plausible. At low Munsell Value, calculated PCCS saturation can also become
very large. Together, these properties can cause very dark colors to be
classified as Vivid or Bright.

Earlier experiments with fixed minimum Value and Chroma requirements for Vivid
and Deep were too blunt. Later rules based on separate global Value and Chroma
thresholds affected too much of the classification plane. The desired change
is specifically localized to the region below the dark PCCS centerpoints.

## Current special-region rules

For each hue, the DKG, DK, and DP representative PCCS centers are translated
into approximate Munsell Value and Chroma coordinates. Those hue-specific
centerpoints define four rules:

1. Above the DP center in Chroma but below it in Value, only DP is eligible.
2. Below the DP center in both Chroma and Value, only DP, D, G, DK, and DKG are
   eligible.
3. Below the DK center in both Chroma and Value, only DK, G, and DKG are
   eligible.
4. Below the DKG center in both Chroma and Value, only DKG is eligible.

The comparisons use strict “less than” and “greater than” tests. More-specific
bottom-left rules take precedence over broader rules. Once the eligible set has
been determined, the classifier selects the nearest remaining PCCS tone center
using the corrected Euclidean distance.

## Interpretation

The rules give the dark tone centers explicit ownership of the area beneath
them without replacing the normal classifier across the rest of the plane.

- A high-chroma color below the DP center becomes Deep instead of continuing
  into an implausible Vivid or Bright region.
- Below DP in both dimensions, several muted and dark alternatives remain
  available rather than forcing every color into one category.
- Moving farther toward the bottom-left progressively removes implausible
  alternatives.
- The darkest, least-chromatic corner ultimately belongs entirely to DKG.

The structure is deliberately asymmetric. The Value rules establish the dark
region rather than imposing a strict hierarchy among DKG, DK, and DP. The
Chroma thresholds progressively narrow the eligible tones because DKG, DK, and
DP have a meaningful ordering along the chroma dimension.

## Why this approach is useful

Modified PCCS retains the existing PCCS tone centers and nearest-center
behavior wherever the special rules do not apply. It therefore acts as a
localized boundary policy rather than a replacement color model.

The thresholds are derived from PCCS’s own representative centers and are
recalculated by hue. This makes the extension more internally connected to the
source system than arbitrary fixed cutoffs such as “Vivid is forbidden below
Value 2.5.”

The result behaves more like a deliberate categorical tone map and less like
an accidental consequence of unbounded Voronoi cells.

## Implementation

`scripts/classify_munsell_pccs.py` supports the optional `--modified-pccs`
argument. When enabled, it appends the following generated field:

```text
PCCS_CATEGORY_MODIFIED_PCCS
```

The generated classifications are stored in:

```text
docs/assets/munsell_renotation_pccs_categories.csv
```

`docs/pccs_voronoi_oklch.html` displays Normal PCCS and Modified PCCS side by
side. The toy approximately translates the PCCS classification field into
fixed-hue OKLCH Lightness–Chroma slices. It uses a nonlinear approximation for
Munsell Value and hue-specific empirical Chroma ratios summarized from the
project’s existing in-sRGB samples.

The OKLCH visualization is a fitted exploratory projection. It is useful for
understanding and debugging the region geometry, but it is not an independent
or authoritative conversion among OKLCH, Munsell, and PCCS.

## Current status

The present rules produce a visually and conceptually promising cleanup of the
problematic lower region. They should remain identified as a project-specific
extension until they have been explored across more hues and practical color
selections.

Future refinement may adjust eligible tone sets or boundary relationships, but
the current design principle should be preserved: modify only the problematic
dark region and leave normal PCCS behavior intact elsewhere.
