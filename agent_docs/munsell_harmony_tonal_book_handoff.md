# MUNSEL HARMONY TONAL BOOK Handoff

## Current experiment

`docs/munsel_harmony_tonal_book.html` is now a palette-generation experiment rather than a diagnostic landmark viewer. It still displays two Munsell hue pages on a shared signed-Chroma grid, but its left sidebar generates and displays two Advanced Extended Palettes for the selected hue pair:

- a Hierarchical Advanced Palette using a Superior Brightest and Inferior Brightest;
- an Equal-Lightness Advanced Palette using a pair of Equal-Lightness Brightests.

The experiment remains a single static HTML page that loads `docs/assets/munsell_renotation_oklch.csv` directly in the browser. Its palette-generation logic is still embedded in the page and is exploratory rather than the reusable headless library anticipated by the project goals.

## Hue-angle selection

The former harmony and harmony-member selectors were replaced by a single hue-angle selector. Each selection produces only one related hue rather than a complete multi-member harmony.

The available relationships are:

- Complement: `20`;
- Split Complement LEFT: `-17`;
- Split Complement RIGHT: `+17`;
- Analog LEFT: `-3`;
- Analog RIGHT: `+3`;
- Quarter LEFT: `-10`;
- Quarter RIGHT: `+10`;
- Thirds LEFT: `-13`;
- Thirds RIGHT: `+13`.

LEFT means a negative offset and RIGHT means a positive offset through the ordered set of 40 discrete Munsell hue pages. The user intentionally chose `13` for Thirds.

## Tonal rules

The active definitions are in `agent_docs/munsell_harmony_book_terminology.md`. Important decisions made during this work include:

- Chroma 2 is treated as achromatic except for Off colors. It cannot be used by a Basic Extended Palette or selected as an Inferior Brightest.
- When a Superior Brightest has no eligible Inferior Brightest, its entire Munsell Value column is excluded and the Superior/Inferior selection is recalculated. This repeats until a valid pair is found or no eligible Value columns remain.
- A Basic Extended Palette starts from each Brightest's `C` line. It expands through `C - 4`, `C - 6`, `C - 8` and so on, and through `C + 4`, `C + 6`, `C + 8` and so on. The immediately adjacent `C - 2` and `C + 2` lines are intentionally omitted.
- On every eligible Chroma line, Value expands from the Brightest using offsets `0`, `+3`, `-3`, `+6`, `-6` and so on in Value Steps until the edges of the book are reached.
- Colors in the Dark Region, achromatic colors, out-of-gamut coordinates, and coordinates beyond the book are excluded.
- The Dark Region remains Munsell Value `0.2` through `0.9`, inclusive.
- A hue's Basic Extended Palette is malformed only if expansion in every eligible direction produces no colors. An invalid coordinate or direction no longer suppresses valid colors in other directions.

## Off colors and Advanced Extended Palettes

Chroma 4 Off colors were abandoned because Off-Black 4 was too unreliable. Only the following Chroma 2 Off colors remain:

- Off-White 2: the greatest-Value Chroma 2 member;
- Off-Gray 2: the Chroma 2 member at Value 6;
- Off-Black 2: the least-Value Chroma 2 member within the inclusive Value range `0.7` through `0.9`.

If the required member does not exist, the palette shows a blank and reports an error. Each Advanced Extended Palette adds these three Off colors for both displayed hues to its Basic Extended Palette.

The older `scripts/validate_munsell_harmony_palettes.py` and `munsell_harmony_palette_validation.csv` predate these rule changes. In particular, they still reflect the earlier finite extension and Chroma 4 Off-Black validation concepts. Treat them as historical generated reference data unless they are deliberately updated later.

## Interface and presentation

- The introductory paragraph, hover inspector, diagnostic box, old landmark key, Opposite behavior, and old highlighting were removed.
- The hue and angle selectors appear above the generated palettes.
- The grid highlights only the two Hierarchical Brightests and the two Equal-Lightness Brightests. A swatch may carry both highlight colors when the methods select the same coordinate.
- Basic Extended colors are sorted by primary hue then related hue, descending Munsell Value, and descending Munsell Chroma.
- Undefined or malformed required members appear as blank patterned swatches and add an error line.
- Each palette has a fixed-height blank error area so errors do not change the layout.
- The palette display retains a fixed capacity of 84 positions. The current rules generate at most 78 colors after removal of the six Chroma 4 Off colors; the unused positions remain invisibly reserved for now.

The preferred local server is Python's HTTP server on port 8000 serving `docs/`. `AGENTS.md` records the command and requires the server to be running after HTML edits.

## Next step

Trim the generated palettes into smaller palettes with clear, identifiable color roles.

The current Advanced Extended Palettes should be treated as candidate pools rather than finished palettes. The next experiment should define useful roles, decide how many colors each role needs, and select role colors from the candidate pool in a way that makes the purpose of every retained color understandable. Preserve the distinction between Hierarchical and Equal-Lightness tonal relationships while exploring whether they need different role-selection rules.
