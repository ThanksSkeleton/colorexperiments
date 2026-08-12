# MUNSEL HARMONY BOOK handoff

## Context and intent

The project is still in the experimentation and learning phase. The next experiment should build on `MUNSEL_BOOK` without turning this work into a generalized or polished application architecture.

The current relevant files are:

- `scripts/munsell_dat_to_oklch_csv.py` — converts `input/all.dat`, adds synthetic Value midpoints, derives OKLCH and sRGB, and normally keeps only in-gamut rows.
- `docs/assets/munsell_renotation_oklch.csv` — published data used in the browser.
- `docs/munsel_book.html` — the existing single-hue book. Its display has Munsell Value horizontally (lightest at left) and Chroma vertically (highest at top).
- `docs/index.html` — experiment index.

Keep the existing spelling convention in experiment names and filenames: `MUNSEL_BOOK` and `MUNSEL_HARMONY_BOOK`, even though the color system itself is spelled “Munsell.”

## Requested work

### 1. Add achromatic generation to the Python converter

Extend `scripts/munsell_dat_to_oklch_csv.py` so it generates Munsell neutral-axis entries in addition to the chromatic renotation rows.

Represent neutral rows unambiguously in the existing schema:

- `H`: `N`
- `C`: `0`
- `MUNSELL_NAME`: conventional neutral notation such as `N 5`
- `OKLCH_C`: zero, subject only to insignificant floating-point noise if the implementation derives it through XYZ
- `OKLCH_h`: blank/undefined, because hue is undefined at zero chroma
- `FAKE_MUNSEL`: `FALSE` for actual neutral Value entries

Use the accepted Munsell neutral Value-to-luminance relationship rather than treating OKLCH lightness as identical to Munsell Value divided by 10. Preserve the script’s existing D65/OKLCH and sRGB conventions. If synthetic half-Value neutrals are generated, mark them consistently with the existing synthetic midpoint convention (`x` in the name and `FAKE_MUNSEL=TRUE`).

The neutral entries need to cover the Values used by the display so that the achromatic strip can align with the chromatic grids. Keep the resulting ordering deterministic.

### 2. Regenerate the published CSV

Run the converter explicitly against the repository input and published asset:

```bash
python3 scripts/munsell_dat_to_oklch_csv.py \
  input/all.dat \
  docs/assets/munsell_renotation_oklch.csv
```

Check the generated CSV programmatically for:

- neutral rows with `H=N` and `C=0`;
- blank neutral `OKLCH_h` values;
- expected real/synthetic flags;
- no accidental loss or schema change to existing chromatic rows.

Project instructions currently prohibit agent-run testing and visual review unless the user explicitly overrides that rule. Do deterministic data inspection only, then give the page to the user to examine.

### 3. Keep `MUNSEL_BOOK` chromatic-only

The existing `docs/munsel_book.html` groups every CSV row by `H`, so adding `H=N` would currently create an unwanted neutral page.

Change its load/grouping logic to explicitly exclude neutral rows. Do not depend on hue sorting behavior to hide them. `MUNSEL_BOOK` should retain exactly its 40 chromatic hue pages and should otherwise continue behaving as it does now.

### 4. Create `MUNSEL_HARMONY_BOOK`

Create a new static color toy, expected at `docs/munsel_harmony_book.html`, and add it to `docs/index.html`.

The central presentation should be a vertically joined harmony layout:

1. A normal page for the selected first hue.
2. The achromatic neutral strip directly beneath it.
3. A page for the selected related hue beneath the neutral strip, rotated 180 degrees—both upside down and horizontally mirrored.

“Upside down and mirrored” should be implemented as a 180-degree rotation of the second hue’s grid. The intent is that the low-chroma edge of both hue grids meets the neutral strip, while their Value directions oppose one another across the composition:

- Top hue in its normal orientation: Value lightest at left; Chroma highest at top and lowest at the neutral seam.
- Neutral strip at the center: Chroma 0, aligned by Value.
- Bottom/other hue rotated 180 degrees: its low-chroma edge meets the neutral seam; its Value order appears reversed relative to the top grid.

Preserve empty cells rather than collapsing unavailable Value/Chroma combinations. All harmony views should use the same fixed global row and column dimensions, as `MUNSEL_BOOK` now does.

Carry over the useful interaction from `MUNSEL_BOOK`:

- hue/page controls;
- compact square swatches labeled only with their Munsell names;
- hover/focus inspector with a large color preview, Munsell name, hex, RGB, OKLCH, and real/synthetic status;
- resetting the inspector to `No Color` and placeholder values when the pointer leaves or focus leaves a swatch.

The exact control for selecting harmony type can remain simple (for example, a `<select>`). No framework is needed.

## Discrete hue geometry

The CSV/book has 40 chromatic hue pages:

- 10 hue families: `R, YR, Y, GY, G, BG, B, PB, P, RP`
- Four positions per family: `2.5, 5, 7.5, 10`
- One page step equals 2.5 Munsell hue units

Treat the ordered page list as circular and calculate harmony members by modular page offsets. No additional hue interpolation is requested.

### Suggested harmonies

- **Adjacent/analogous:** neighboring pages. Offer a modest discrete span such as ±1 page; ±2 or ±3 pages can be considered if a width control is useful, but Munsell has no single canonical analogous distance.
- **Complement:** `+20` pages. This is exactly halfway around the 40-page circle.
- **Right angle:** `+10` pages (or `-10` for the other direction).
- **Square:** four members at offsets `0, +10, +20, +30`.
- **Triad:** use successive steps of **13, 14, 13** pages around the circle. Starting from page `p`, the members are `p`, `p+13`, and `p+27`; the final 13-page step returns to `p` modulo 40. Do not interpolate an exact one-third-circle hue.
- **Split complement:** select pages symmetrically on either side of the `+20` complement. Munsell supplies no canonical split distance, so keep the offset explicit and discrete (for example, complement ±1 page as the narrowest option).

For the initial two-hue composition, complement, right-angle, analogous, and either branch of split complement each naturally yield an “other hue.” Square and triad have more than one related hue; a simple member selector or cycling control is sufficient. Avoid inventing interpolated hue pages.

## Completion checklist

- Neutral-axis generation is part of the Python converter rather than browser-only fabrication.
- The published CSV has been regenerated with neutral rows.
- `MUNSEL_BOOK` still exposes only the original 40 chromatic pages.
- `MUNSEL_HARMONY_BOOK` shows the selected hue, centered neutral strip, and 180-degree-rotated related hue.
- Harmony calculations wrap correctly around the 40-page list.
- Triads use `13, 14, 13` page steps.
- The new experiment is linked from `docs/index.html`.
- No visual review or agent-run tests are performed unless the user changes the project instruction.
