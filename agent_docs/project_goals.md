# Color Experiments Project Goals

## Project intent

Collect, organize, and present a set of pre-existing interactive HTML color experiments originally created through ChatGPT conversations.

The project is primarily for the author's own thinking and use, with a secondary goal of sharing the experiments with friends for a casual “gee whiz” reaction. It should be candidly presented as vibe-coded or AI-coded work rather than as wholly original authorship.

## Phase 1: Current priorities

1. Publish the existing experiments as a simple static website.
2. Provide a project landing page that links to every experiment.
3. Host the public site with GitHub Pages from the repository's `docs/` directory.
4. Host the source in a public GitHub repository.
5. Extract duplicated color-conversion and color-analysis code into shared TypeScript modules.
6. Clean up the experiments' code, layout, filenames, and styling incrementally without turning the project into an overly polished product.

## Phase 2: Speculative ideas

1. Add further color experiments as ideas emerge.
2. Use the shared color TypeScript code in a non-experimental project authored by the repository owner.

These ideas are intentionally lower priority and are not commitments.

## Underlying goals

- Compile and organize the experiments for personal reference.
- Make the AI-assisted origin clear and keep the presentation low-ego.
- Make the experiments easy to share with personal friends.
- Preserve the playful, exploratory character of the original work.

## Non-goals

- Presenting the project as résumé material or professional-development work.
- Claiming the generated experiments as wholly original work.
- Making the site highly polished, formal, or product-like.
- Presenting the experiments as pedagogical, academic, or scientific material.
- Adding server-side infrastructure when static hosting is sufficient.

## Current technical direction

- Static HTML, CSS, and browser JavaScript published from `docs/`.
- Shared code authored in TypeScript under `src/` and compiled into `docs/assets/`.
- Minimal tooling: Node.js, npm, and the project-local TypeScript compiler.
- No application framework unless later experiments provide a concrete reason to add one.

