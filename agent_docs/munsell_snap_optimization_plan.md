# MUNSEL SNAP proposed optimization plan

## Rendering goal

MUNSEL SNAP keeps continuous OKLCH geometry and cursor coordinates, but renders
each in-sRGB-gamut map pixel with the uniform display color of its nearest Munsell
renotation. Nearest means Euclidean distance in OKLab, matching the Delta E used
by the OKLCH Harmony Inspector:

```text
Delta E = sqrt((Delta L)^2 + (Delta a)^2 + (Delta b)^2)
```

The result should look like the original slice geometry divided into discrete,
uniform Munsell regions. Saved and proposed colors retain both the underlying
continuous OKLCH color and the corresponding snapped Munsell entry.

## Proposed optimizations

### 1. Prepare the Munsell dataset once

Load and parse the generated CSV once when the page starts. The converter excludes
the singular and out-of-sRGB rows by default and adds synthetic OKLCH-interpolated
Munsell Value midpoints marked `FAKE_MUNSEL=TRUE` and with names ending in `x`.
The page restricts snapping candidates to entries marked `IN_SRGB_GAMUT=TRUE`.
Precompute and retain each candidate's:

- Munsell hue, value, and chroma
- OKLCH coordinates
- Cartesian OKLab coordinates
- normalized sRGB coordinates and display bytes

Restricting the index to displayable renotations prevents an in-gamut underlying
pixel from snapping to a Munsell color that the sRGB canvas cannot reproduce.

### 2. Use an exact OKLab nearest-neighbor index

Build a three-dimensional k-d tree over the precomputed OKLab points. Euclidean
OKLab Delta E is Cartesian distance in three dimensions, so a standard k-d tree
can return the exact nearest entry without scanning every candidate for every
pixel.

### 3. Cache rendered slice images

Cache the posterized base image independently from cursor overlays. The left base
depends only on fixed lightness; the right base depends only on fixed hue. Saved
and proposed guides can then be redrawn cheaply without recomputing posterization.

Only the opposite slice needs a new base during interaction: changing hue on the
left affects the right base, while changing lightness on the right affects the
left base.

### 4. Quantize only the rendered slice parameter

Keep cursor coordinates and nearest-Munsell selection exact, but optionally cache
background slices using small fixed-coordinate steps, such as 1 degree of hue and
0.005 lightness. A bounded least-recently-used cache could retain only recent
slices rather than every possible slice.

### 5. Use a controlled internal rendering resolution

If necessary, compute the posterized maps at a lower internal resolution and
scale them to their displayed dimensions. Uniform Munsell regions may tolerate
this better than smooth gradients, but the effect on boundary shapes should be
judged in the browser.

### 6. Keep cursor snapping separate from map rendering

Perform one exact k-d-tree lookup for the current cursor proposal independently
of any background caching or quantization. This keeps proposed and saved OKLCH
coordinates and their Munsell matches exact even if map rendering is later
approximated for speed.

### 7. Move base rendering to a worker if needed

If optimized synchronous rendering still interrupts pointer interaction, generate
posterized pixel buffers in a Web Worker. Keep overlays and readouts on the main
thread so interaction remains responsive.

## Initial implementation decision

Start with optimizations 1 and 2 only: prepare the filtered dataset once and use
an exact OKLab k-d tree. Evaluate how far those changes take performance before
adding caching, quantization, reduced resolution, separated rendering work, or a
Web Worker. Those later options remain proposals rather than current behavior.

## Initial implementation observation

The implementation using optimizations 1 and 2 is "not impressive" in
performance, but remains usable for the project's exploratory work. Later
optimizations should remain available if interaction cost begins to interfere
with the experiment.

The first posterized maps also expose two geometric issues for the intended use:

1. A fixed OKLCH hue slice can straddle two Munsell hue slices. This is currently
   a minor concern.
2. A fixed OKLCH lightness slice can straddle two Munsell Value slices. This is a
   major concern.

When OKLCH remains the coordinate system, the nearest-renotation regions behave
like irregular bricks: their sides do not align cleanly with constant OKLCH hue,
and their tops and bottoms do not align cleanly with constant OKLCH lightness or
have consistent OKLCH height. Consequently, colors selected as OKLCH hue
opposites can snap to Munsell bricks with noticeably different displayed
lightness even when their underlying OKLCH lightness is held constant.
