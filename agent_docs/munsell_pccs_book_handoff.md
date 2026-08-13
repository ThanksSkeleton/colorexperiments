# MUNSEL PCCS BOOK Handoff

## Purpose of this exploration

This side exploration examines how PCCS tone categories relate to the Munsell
colors used by the existing MUNSEL HARMONY BOOK experiments. The immediate
artifact is a new static experiment, `docs/munsel_pccs_book.html`, which maps
PCCS category labels onto the two-hue signed-Chroma Munsell grid.

The experiment is diagnostic rather than authoritative. It currently exposes
five competing classifications because investigation revealed substantial
problems with both the original third-party implementation and the policy used
to turn the 2001 paper's continuous tone coordinates into discrete labels.

## Source material

The PyPI package `pccs` 0.2a3 and its dependencies were downloaded into the
gitignored uppercase `INPUT/` directory. The repository also has a separate,
pre-existing lowercase `input/` directory. Both are ignored.

The package is an MIT-licensed 2021 alpha release by Masaaki Shibata. Its core
implementation is a single Python module based on:

> M. Kobayasi and K. Yosiki. 2001. “Mathematical Relation among PCCS Tones,
> PCCS Color Attributes and Munsell Color Attributes.” Journal of the Color
> Science Association of Japan 25 (4), 249–261.

The upstream package cannot run normally with current `colour-science` because
it imports names that have since been removed or renamed. It also has no useful
test suite beyond documentation examples.

Later, the user supplied `INPUT/munsell_to_pccs.py`. ChatGPT had produced that
script after reading the 2001 paper. It independently transcribes the paper's
coordinate formulas and adds Euclidean nearest-center classification as an
explicit policy not prescribed by the paper.

## Standalone bulk classifier

`scripts/classify_munsell_pccs.py` is a standard-library-only bulk CSV
classifier extracted from the original package. It does not require NumPy,
SymPy, `colour-science`, or the third-party `pccs` package.

The script:

- reads a CSV containing Munsell `H`, `V`, and `C` columns;
- performs the continuous Munsell-to-PCCS coordinate conversion;
- replaces the original SymPy quadratic solve with its explicit positive root;
- preserves the original package's half-step rounding when requested;
- preserves the original package's unusual tone-distance formula when
  requested;
- provides a corrected squared-Euclidean distance formula;
- adds a Paper-2001-derived classification using the independently supplied
  transcription;
- writes category labels only, not intermediate PCCS coordinates;
- retains the upstream MIT copyright and permission notice.

The command used to generate the published asset is:

```sh
python3 scripts/classify_munsell_pccs.py \
  docs/assets/munsell_renotation_oklch.csv \
  --output docs/assets/munsell_renotation_pccs_categories.csv \
  --distance-formula both \
  --rounding both
```

An ignored working copy was also generated at
`INPUT/munsell_pccs_categories.csv`.

## Classification variants

The generated CSV currently has five category columns:

1. `PCCS_CATEGORY_OLD_DISTANCE_OLD_ROUNDING`
2. `PCCS_CATEGORY_OLD_DISTANCE_NEW_ROUNDING`
3. `PCCS_CATEGORY_NEW_DISTANCE_OLD_ROUNDING`
4. `PCCS_CATEGORY_NEW_DISTANCE_NEW_ROUNDING`
5. `PCCS_CATEGORY_PAPER_2001`

In the UI these are shown as:

- Old distance · Half-step;
- Old distance · Continuous;
- Corrected distance · Half-step;
- Corrected distance · Continuous;
- Paper 2001 transcription.

“Old rounding” means the original package's behavior of rounding PCCS hue,
lightness, and saturation to the nearest 0.5 before tone classification. “New
rounding” means no rounding: continuous coordinates are classified directly.

The old distance formula is:

```text
((reference saturation - saturation)^2
 + (reference tone-lightness - tone-lightness))^2
```

This permits a negative lightness difference to cancel a positive squared
saturation difference. The corrected formula is ordinary squared Euclidean
distance:

```text
(reference saturation - saturation)^2
+ (reference tone-lightness - tone-lightness)^2
```

The Paper 2001 column also uses continuous coordinates and Euclidean distance,
but corrects a significant chroma-conversion transcription error inherited
from the rejected library. The original package calculates:

```text
12 + 1.7 * sin(h + 2.2*pi/12)
```

The independently transcribed paper equation is:

```text
12 + 1.7 * sin((h + 2.2)*pi/12)
```

The integrated fifth-column implementation was checked against
`INPUT/munsell_to_pccs.py` for every chromatic input row and produced zero
mismatches.

## Why the original Python package was rejected

The user rejected the package as a reliable PCCS guide after a spot check of
Munsell `7.5B 8/8`.

The original package itself returns:

```text
PCCS coordinates after rounding: h=16.5, l=8.0, s=7.5
Tone: dk (Dark)
Short label: dk16.5
```

Our extracted Old–Old variant returns the same answer, proving that extraction
did not introduce the error. The other three original-package-derived variants
return `lt+` (Light Plus).

The old distance formula makes Dark appear artificially close because:

```text
((5 - 7.5)^2 + (3 - 9.3593))^2
= (6.25 - 6.3593)^2
```

The unrelated saturation and lightness differences almost exactly cancel.
This is perceptually implausible and mathematically unsuitable as a distance.
The later discovery of the chroma-term parenthesis error further undermined
the package.

## Four-variant comparison

Before the Paper 2001 column was added, all four combinations were compared
over 3,395 Munsell rows:

- 2,132 rows (62.8%) received the same category in all four variants;
- 1,263 rows (37.2%) differed in at least one variant;
- rounding changed 497 results with old distance;
- rounding changed 197 results with corrected distance;
- correcting distance changed 1,060 results with half-step rounding;
- correcting distance changed 1,071 results with continuous coordinates.

The distance formula therefore had a much larger effect than rounding. The
corrected distance was also less sensitive to rounding.

## Paper 2001 versus New–New

The Paper 2001 transcription was compared with corrected-distance/continuous,
called New–New during discussion:

- total rows: 3,395;
- exact matches: 2,752;
- differences: 643;
- disagreement rate: 18.94%;
- neutral categories were unchanged.

Frequent New–New to Paper-2001 transitions included:

- `dp` to `dk`: 46;
- `lt` to `lt+`: 46;
- `b` to `lt+`: 43;
- `v` to `b`: 41;
- `dkg` to `dk`: 33;
- `v` to `s`: 32;
- `lt+` to `b`: 32.

For the earlier `7.5B 8/8` spot check, both New–New and Paper 2001 return
`lt+`.

## MUNSEL PCCS BOOK interface

`docs/munsel_pccs_book.html` is linked from `docs/index.html` and loads
`docs/assets/munsell_renotation_pccs_categories.csv`.

The page retains the useful structure of the MUNSEL HARMONY BOOK:

- two hue pages on one signed-Chroma grid;
- Munsell Value from lightest to darkest;
- primary hue on positive Chroma rows;
- neutrals at Chroma zero;
- related hue on negative Chroma rows;
- hue, harmony, and harmony-member selectors;
- previous/next hue navigation;
- hover/focus inspection.

It adds:

- a selector for all five classification variants;
- a stable outline color for every PCCS category;
- component-aware perimeter outlines;
- one label in every connected component;
- a legend;
- a summary of the number of regions and multiply disconnected categories on
  the current combined page.

## Contiguity finding

The initial assumption that each category would form one contiguous region on
a hue page was false. Four-neighbor adjacency was used; diagonal contact did
not count.

For the original four variants, the audit found:

- Old distance + half-step: 309 disconnected category groups out of 532;
- Old distance + continuous: 299 out of 536;
- Corrected distance + half-step: 54 out of 508;
- Corrected distance + continuous: 57 out of 504.

Some legacy classifications split one category into as many as seven
components on a hue page. The renderer therefore does not assume contiguity.
It flood-fills every category component and draws boundaries wherever an
orthogonal neighbor is missing or belongs to another category.

## Low-Value “Vivid” problem

The largest unresolved issue is that all five variants classify some very dark
purple and blue colors as Vivid. The clearest example is Munsell
`7.5PB 0.2/4`.

The Paper 2001 transcription calculates:

```text
PCCS hue h:                 19.4208
PCCS lightness l:            0.2
PCCS saturation s:          14.3944
Tone-relative lightness t:   3.5028
```

Euclidean distances to the nearest centers are approximately:

```text
Vivid: 5.752
Deep:  6.422
Strong: 6.616
Bright: 7.105
Dark:  9.408
```

Vivid wins only because the calculated saturation is far beyond the tone
centers' normal range. It is not actually close to any center.

The immediate mathematical cause is the saturation conversion's factor:

```text
1 - exp(-gamma * V)
```

in the denominator. As Munsell Value approaches zero, that factor approaches
zero, so any fixed nonzero Chroma produces unbounded PCCS saturation. At the
same hue and Chroma:

```text
V=0.1 -> s=22.21 -> Vivid
V=0.2 -> s=14.39 -> Vivid
V=0.3 -> s=11.16 -> Deep
V=0.4 -> s=9.34  -> Deep
V=0.7 -> s=6.76  -> Dark
V=0.9 -> s=5.94  -> Dark
```

The paper describes the most vivid realizable colors as approximately `s=9`
and its reference grid as roughly `s=1...10`. The supplied script performs no
range check after conversion.

The paper derives a hue-independent `(s,t)` tone-coordinate system and lists
14 representative tone centers. It does **not** prescribe Euclidean
nearest-center classification. It says that tone regions should be set
appropriately, giving dotted boundaries in Figure 13 as an example. The
Euclidean Voronoi policy was added by the supplied ChatGPT-generated script.

Therefore `7.5PB 0.2/4 -> Vivid` is:

- not a formula transcription error in the supplied script;
- not a conclusion explicitly made by the paper;
- partly an extrapolation failure near absolute black;
- primarily an inadequacy of forcing out-of-range coordinates into the
  nearest representative tone center;
- made stranger by applying the hue shear at an abnormally large saturation.

## Recommended next exploration

Create a separate diagnostic toy for tone-boundary policy rather than changing
the current book immediately. It should make the `(s,t)` plane and the
low-Value singularity visible.

Questions to investigate include:

1. What is the valid input/output domain of the paper's conversion?
2. Should `s > 9`, `s > 10`, or another condition produce an explicit
   “outside modeled PCCS range” result?
3. Can the boundary shapes in Figure 13 be reconstructed or approximated?
4. Should Vivid and Bright regions have explicit lower-lightness boundaries?
5. Should Deep or Dark absorb high-saturation points below those boundaries?
6. Would a non-Euclidean metric help, or are explicit categorical regions and
   domain constraints more appropriate?
7. How should missing/out-of-book Munsell regions affect interpretation?
8. Can an authoritative PCCS region chart or reference set be acquired for
   validation?

The current best working interpretation is that non-Euclidean distance alone
is unlikely to solve the entire problem. Explicit domain handling and explicit
tone regions are probably required.

## Verification state

The generated published CSV contains 3,395 data rows and five nonempty category
columns. All values belong to the expected category set. The fifth column
matches the supplied Paper-2001 script exactly for all chromatic rows.

The inline JavaScript parses successfully, and the page and asset were served
successfully with HTTP 200. A headless Firefox load check could not be completed
because the installed Firefox Snap could not create its mount namespace in the
execution environment. No multimodal visual review was performed.

The preferred local server is:

```sh
python3 -m http.server 8000 --directory docs
```

At the end of this conversation it was running on port 8000, and the page was
available at:

```text
http://localhost:8000/munsel_pccs_book.html
```

## Current status

The five-way MUNSEL PCCS BOOK is complete as a diagnostic comparison tool. None
of its five classifiers should yet be treated as an authoritative PCCS tone
classifier. The original package is rejected; the Paper 2001 transcription is
a better coordinate foundation but still needs a defensible domain and
categorical-boundary policy.
