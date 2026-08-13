# PCCS Chroma Exploration Summary

## Purpose

This exploration investigates why the experimental Munsell-to-PCCS classifier
assigns implausible PCCS tone labels to some very dark colors, especially Vivid
labels in purple and blue regions.

The working conceptual hierarchy for this exploration is deliberately simple:

- OKLCH is the project's mathematical home and preferred approximately
  perceptually uniform coordinate system.
- Munsell is treated as an artist-oriented color organization with historical
  and practical compromises.
- PCCS is treated as an artist-oriented categorization built from Munsell
  coordinates.

This framing papers over important distinctions among color appearance,
physical samples, viewing conditions, and perceptual-uniformity claims. That is
acceptable for the present exploratory purpose.

## Starting problem

The five classifiers displayed in `docs/munsel_pccs_book.html` assigned Vivid
to some extremely dark Munsell colors. The clearest example was Munsell
`7.5PB 0.2/4`.

The Paper 2001 transcription converts Munsell Chroma to PCCS saturation using
a Value-dependent denominator containing:

```text
1 - exp(-gamma * V)
```

As Munsell Value approaches zero, this denominator approaches zero. Any fixed
nonzero Munsell Chroma therefore produces unbounded PCCS saturation. A
nearest-center classifier must still choose one of the representative PCCS
tone centers even when the converted point is far outside their normal range.
At sufficiently high calculated saturation, Vivid can become the least-distant
center despite remaining a poor match in absolute terms.

The earlier `agent_docs/munsell_pccs_book_handoff.md` contains the detailed
classifier history, formulas, comparisons, and package evaluation.

## First diagnostic toy

`docs/pccs_value_chroma.html` was initially created as a reduced Munsell book.
For each hue it showed only:

- Munsell Chroma `4`;
- Munsell Chroma `2`;
- the achromatic axis, Chroma `0`.

It provided left and right selection modes for comparing two samples with
different Munsell Values. The diagnostic showed each sample's OKLCH Chroma and
the signed and absolute OKLCH Chroma differences.

The comparison exposed that a fixed Munsell Chroma does not map to a fixed
OKLCH Chroma. In some cases, the OKLCH Chroma difference between a very light
`C2` sample and a very dark `C2` sample was comparable to the difference
between Munsell `C2` and `C4` at one Value.

## Chroma and saturation interpretation

The exploration adopted the following practical distinction:

- Chroma describes departure from a neutral of comparable lightness.
- Saturation describes chromatic strength relative to the color's own
  brightness or lightness.

Munsell Chroma and OKLCH Chroma address the same broad idea but use different
perceptual maps and different geometries. Equal Munsell Chroma does not imply
equal OKLCH Chroma. Neither necessarily implies equal saturation.

The observed very dark samples can therefore appear highly saturated relative
to their limited light output without necessarily having exceptionally high
absolute OKLCH Chroma. Some increase in a PCCS saturation-like coordinate near
black is conceptually reasonable. The unresolved problem is the conversion's
unbounded magnitude and the classifier's forced assignment to a normal tone
center.

## OKLCH Chroma/Lightness diagram

The comparison interface was replaced with a fixed-hue OKLCH diagram:

- horizontal axis: OKLCH Chroma;
- vertical axis: OKLCH Lightness;
- colored circles: available Munsell samples at their OKLCH coordinates;
- solid white curves: interpolations through equal-Munsell-Chroma samples;
- dashed white curves: interpolations through equal-Munsell-Value samples;
- shared achromatic samples: `C0` anchors for the Value curves;
- one mouseover/focus inspector for sample details;
- hue selection through a dropdown and previous/next buttons.

The white curves use simple smooth interpolation through the existing points.
They visualize the mapping but are not rigorous fitted boundaries or a new
color model.

This diagram made the sub-Value-1 region visibly exceptional. Constant-Munsell-
Chroma curves bend sharply when represented in OKLCH, revealing that the very
dark extension has substantially different geometry from the ordinary working
range.

## Status of Munsell Values below 1

Munsell Value `0` is theoretical black. Ordinary practical descriptions begin
with the darkest gray around Value `1`. Renotation coordinates for Values
`0.8`, `0.6`, `0.4`, and `0.2` come from a specialized 1956 extension of the
Munsell renotation system to very dark colors.

That extension intentionally continues constant-Chroma loci toward black even
when doing so requires increasingly extreme chromaticities and eventually
extends beyond physically realizable surface colors. The sub-1 coordinates are
published parts of an idealized renotation extension, but they are not ordinary
Munsell Book samples in the same practical sense as the main Value range.

This makes the sub-1 region historically meaningful but poorly suited to the
present PCCS application investigation. Combining its unusual geometry with
the PCCS saturation singularity overwhelms the more practically relevant
classification behavior.

## Project decision: use Munsell Value 1 and above

The project now treats Munsell Value `1` as the lower boundary of its practical
Munsell domain.

The implementation includes:

- removal of all rows below Value `1` from
  `docs/assets/munsell_renotation_oklch.csv`;
- regeneration of `docs/assets/munsell_renotation_pccs_categories.csv` from the
  reduced Munsell data;
- source filtering in `scripts/munsell_dat_to_oklch_csv.py` before midpoint or
  neutral generation;
- output filtering in `scripts/classify_munsell_pccs.py` even when supplied a
  broader input file;
- defensive `V >= 1` filtering in every Munsell data-driven browser toy;
- removal of the special `V0.2–0.9` Dark Region from the tonal palette logic;
- selection of the darkest remaining eligible sample for off-black;
- suppression of Munsell Value contours and readouts below `V1` in the
  standalone OKLCH/Munsell Value contour toy.

The standalone contour toy continues to display its underlying OKLCH plane
below the boundary because that plane is OKLCH data, not a display of supported
Munsell coordinates.

The detailed rationale and implementation policy are recorded in
`agent_docs/Munsel Less than 1 removed.md`.

## What this resolves

The cutoff removes the most pathological part of the low-Value PCCS result:
the specialized theoretical Munsell tail in which the PCCS saturation formula
diverges most dramatically.

It also makes the working dataset more representative of the way the project
expects to use Munsell and PCCS artistically. Diagnostics are no longer
dominated by colors below the ordinary practical Munsell range.

## What remains unresolved

The Value cutoff does not fully resolve the PCCS Vivid issue. Some purple and
blue samples at Value `1` and above still appear to receive questionable Vivid
labels.

The remaining investigation is more manageable and should focus on:

1. Whether the Paper 2001 coordinate conversion remains trustworthy throughout
   the retained Munsell range.
2. Whether calculated PCCS saturation needs an explicit upper domain boundary.
3. Whether Vivid and Bright need lower-lightness boundaries rather than
   unbounded nearest-center Voronoi regions.
4. Whether Deep or Dark should absorb high-saturation points below those
   lightness boundaries.
5. Whether Figure 13 or another authoritative PCCS tone-region reference can
   support explicit categorical regions.
6. Whether the remaining purple behavior is primarily a coordinate-conversion
   issue, a tone-boundary issue, or a genuine difference between PCCS and the
   project's OKLCH-centered visual judgment.

The current best interpretation remains that changing the distance metric
alone is unlikely to be sufficient. Explicit valid-domain handling and
explicit tone regions are more promising than forcing every coordinate into
the nearest representative center.

