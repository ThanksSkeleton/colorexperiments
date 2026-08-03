# Todo: Artistic Light and Shadow Color Mixes

## Status

Future experiment idea. This is exploratory and not a Phase 1 commitment.

## Core idea

Explore an artistic approach to shading a scene with color:

- Choose a color for the light.
- Mix that light color into the scene's lit areas.
- Rotate the light hue exactly 180 degrees around the color wheel to find its complement.
- Mix that complementary color into the scene's shadowed areas.

The experiment should make it easy to see how one chosen light color produces a related pair of treatments: its own hue in the light and its opposite hue in the shadows.

This is an artistic color-treatment experiment, not a physically accurate simulation of colored lights or shadows.

## Possible experiment

Display a simple scene or illustration with clearly separated light and shadow regions. Let the user choose a light hue and immediately update:

- The lit regions using mixtures with the selected light color.
- The shadow regions using mixtures with the 180-degree complementary hue.
- Color swatches showing the original local color, the light mixture, and the shadow mixture.
- A color wheel showing the light and shadow hues opposite one another.

## Controls to explore

- Light hue.
- Strength of the light-color mixture in lit areas.
- Strength of the complementary-color mixture in shadowed areas.
- Light and shadow value adjustments independent of their hue mixtures.
- Saturation of the light and complementary shadow colors.
- Choice of base colors or scene.
- Toggle between the colored treatment and a neutral light-and-shadow treatment.

## Questions to investigate

- How strongly can the light and complementary shadow colors be mixed before the scene's local colors are lost?
- Should the light and shadow mixture strengths be linked or independently adjustable?
- Does the exact 180-degree complement always produce an appealing result across different base colors?
- How do hue mixing and ordinary value changes work together to preserve readable lighting?
- Is the relationship clearest on a single object, a small scene, or a grid of base-color swatches?
- Which mixing model best reflects the intended artistic result: direct RGB interpolation, perceptual color-space interpolation, blend modes, or another approach?

## Example hue pairs

- Warm orange light with cool blue shadows.
- Yellow light with violet shadows.
- Green light with magenta shadows.
- Red light with cyan shadows.

## Implementation note

Prefer a self-contained static browser experiment that can later use the project's shared TypeScript color utilities. Keep it playful and exploratory rather than presenting the artistic rule as physically accurate, scientific, or universally prescriptive.
