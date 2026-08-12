# MUNSEL HARMONY BOOK Experimental Terminology

These are experimental, contingent working definitions for exploring Munsell color harmonies. They are specific to this exploration and are not part of the project's global glossary.

## Working Universe

Unless a definition explicitly says otherwise, this exploration uses a simplified finite universe consisting only of the samples in the MUNSEL HARMONY BOOK. A sample either exists in this universe and is In Gamut, or it does not exist and is out of gamut. The definitions do not distinguish among theoretical Munsell coordinates, physically realizable colors, and colors excluded specifically by sRGB. References to hue mean a discrete Munsell hue page, and references to lightness mean Munsell Value. These assumptions should not be repeated in every definition.

For Opposites and all derived forms of Opposites, an achromatic input returns `[undefined, undefined]`. An achromatic target is not a valid Opposite; if no chromatic target can be found, the target is `undefined`.

## Rules

- Chroma 2 is treated as achromatic except when selecting an Off-White 2, Off-Black 2, or Off-Gray 2. Therefore, Chroma 2 is not eligible for an extended palette or as an Inferior Brightest.
- If no Inferior Brightest can be found for a Superior Brightest, exclude that Superior Brightest's Munsell Value column and recalculate the Superior Brightest and Inferior Brightest. Repeat this process until a valid pair is found or no eligible Value columns remain.

## Brightest

A family of context-dependent palette anchors. A Brightest may be a Superior Brightest, an Equal-Lightness Brightest, or an Inferior Brightest. Palette rules must specify which Brightest relationship they use.

## Superior Brightest

Among the in-gamut samples for the same discrete Munsell hue, the color with the greatest Munsell Chroma; if multiple colors are tied, the one with the greatest Munsell Value. Chroma takes priority over Value, so a darker color with greater Chroma is considered Brighter than a lighter color with less Chroma.

## In Gamut

A sample in the MUNSEL HARMONY BOOK that is representable within the sRGB gamut. Membership in the book's sample set establishes that the color is within the working Munsell gamut and is physically possible; therefore, for this exploration, sRGB representability is the remaining operational test.

## Equal-Lightness Brightest(s)

Given a hue, a specific harmony, and a specific harmony member, select the Opposite pair having the greatest shared Chroma. If multiple pairs tie, select the pair with the greatest Value.

## Opposites

Given a specific color, a specific harmony, and a specific harmony member, its Opposite is the color in that harmony member having the same Chroma and Value. Return an ordered pair containing the input color first and its Opposite second. If the Opposite is out of gamut, the second member is `undefined`. “Opposite” does not necessarily mean a complementary hue.

## Chroma-Clipped Opposites

Given a specific color, a specific harmony, and a specific harmony member, first seek its Opposite. If the Opposite is out of gamut, reduce the target's Chroma in Steps of 2 without changing its Value until an in-gamut chromatic sample is found. Return the ordered pair containing the unchanged input color first and the resulting target second. If reducing the target would reach Chroma 0 without finding an in-gamut chromatic sample, the target is `undefined`.

## Self-Chroma-Clipped Opposites

Given a specific color, a specific harmony, and a specific harmony member, first seek its Opposite. If the Opposite is out of gamut, reduce the Chroma of both requested coordinates in Steps of 2, without changing their Value, until in-gamut samples for both hues are found. Return the resulting ordered pair, whose members remain Opposites. Chroma 0 is not eligible. If no shared chromatic coordinate exists at that Value, return `[undefined, undefined]`.

## Off-White 2 / Off-Black 2 / Off-Gray 2

For a given hue, each Off color has exactly Chroma 2:

- **Off-White 2:** the color at Chroma 2 with the greatest Value.
- **Off-Black 2:** among the colors at Chroma 2 with Values from 0.7 through 0.9, inclusive, the color with the least Value. If no Chroma 2 member exists within that Value range, the Off-Black does not exist and the result is `undefined`.
- **Off-Gray 2:** the color at Chroma 2 and Value 6.

If the required sample does not exist, the result is `undefined`.

## Dark Region

For a given hue, the colors with Munsell Values from 0.2 through 0.9, inclusive.

## Step

The standard increment used by tonal operations outside the Dark Region. One Value Step is 0.5 Munsell Value, and one Chroma Step is 2 Munsell Chroma. Step terminology and Step-based operations are not allowed within the Dark Region; exact coordinates must be used there instead.

## Successful Palette

Given an input color and a color-collection relationship, the resulting palette is Successful if every required palette member is defined. Equivalently, the result contains no `undefined` members.

## Symmetric Harmony

A harmony for which choosing any of its members as the new input and reapplying the harmony rule produces the same unordered collection of discrete Munsell hue pages.

## Asymmetric Harmony

A harmony that is not symmetric.

## Hierarchical Tonal Relationship

A requested palette-generation relationship that assigns one hue the primary role and another hue the supporting role. The primary hue contributes its Superior Brightest. The supporting hue contributes its Inferior Brightest, constrained to the primary color's Value and to no more than the primary color's Chroma. The selected Chromas may tie; hierarchy describes the assigned roles and constraints rather than requiring a strict inequality in the resulting palette.

## Equal Tonal Relationship

A requested palette-generation relationship that treats both hues as peers. The hues contribute their Equal-Lightness Brightests, selected jointly at the greatest shared Chroma and, when tied, the greatest Value. An Equal Tonal Relationship and a Hierarchical Tonal Relationship may sometimes produce the same colors even though they use different roles and selection rules.

## Inferior Brightest

Given the Superior Brightest of a main hue and a supporting hue in a harmony, the Inferior Brightest is found at the Superior Brightest's Value. Starting from the Superior Brightest's Chroma, reduce Chroma in Steps until an in-gamut color of the supporting hue is found. If no chromatic supporting color exists at that Value, the Inferior Brightest is `undefined`.

## Hierarchical Brightest(s)

Given a main hue and a supporting hue in a harmony, the pair containing the main hue's Superior Brightest and the supporting hue's Inferior Brightest. This pair is the anchor returned by a Hierarchical Tonal Relationship request.

## Basic Extended Palette

Starting from each Brightest color in a hue-harmony member pair, use the Brightest's own Chroma line (`C`) and expand in both Chroma directions beginning two Chroma Steps away: `C - 4`, `C - 6`, `C - 8`, and so on toward the achromatic axis, and `C + 4`, `C + 6`, `C + 8`, and so on toward the edge of the book. The immediately adjacent `C - 2` and `C + 2` lines are not used. On each eligible line, begin at the Brightest's Value and expand in both Value directions in increments of three Value Steps: `0`, `+3`, `-3`, `+6`, `-6`, and so on until the edges of the book are reached. Positive Value offsets are lighter and negative Value offsets are darker. Exclude out-of-gamut colors, colors in the Dark Region, achromatic colors, and colors for which the Chroma reduction crosses through the achromatic axis into the other displayed hue.

## Malformed Basic Extended Palette

A Basic Extended Palette is Malformed for a hue only when expanding from that hue's Brightest in every eligible Chroma and Value direction produces no colors. Reaching Chroma 0, crossing the achromatic axis, encountering Chroma 2, entering the Dark Region, reaching an out-of-gamut coordinate, or reaching an edge of the book excludes only the affected coordinate or direction; it does not prevent generation in the remaining directions. If no eligible colors remain after all exclusions, include a blank for that hue and report an error.

## One-Sided Basic Extended Palette

A Basic Extended Palette containing either only its equal-and-darker colors (Value offsets `0`, `-3`, `-6`, and `-9`) or only its equal-and-lighter colors (Value offsets `0`, `+3`, `+6`, and `+9`).

## Advanced Extended Palette

A Basic Extended Palette with Off-White 2, Off-Black 2, and Off-Gray 2 colors added.
