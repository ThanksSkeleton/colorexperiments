# Paper Doll Experiment Goals

## Purpose

The Superhero Palette Paper Doll Generator is a small prototype for generating and exploring character color palettes. A single base color drives several palettes, which are assigned to simple layered paper-doll figures as a rudimentary preview.

## Functional goals

- Generate several complete palettes from one base OKLCH color.
- Associate colors with character roles such as costume, hair, eyes, skin, and powers.
- Preview role assignments on male and female paper dolls.
- Display palette swatches and detailed, copyable color information.
- Expose constants used to tune palette generation.
- Keep the experiment small and easy to modify.

## Original technical goals

- Separate the original standalone prototype into HTML, script, data, and image files.
- Store paper-doll images as ordinary assets rather than embedded data.
- Keep the implementation understandable without introducing elaborate architecture.

## Non-goals

- Production-grade architecture or long-term support guarantees.
- Server-side infrastructure.
- A highly polished or formal product.
