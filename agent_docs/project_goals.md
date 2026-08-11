# Color Experiments Project Goals

## Project intent

Use a collection of interactive color experiments to explore how formal color systems can support intuitive and aesthetically coherent color selection. Develop the resulting ideas into reusable, headless color-selection code and apply that code to superhero color schemes.

The project is primarily for the author's own enjoyment and understanding, with some practical use in tabletop role-playing games and a secondary goal of sharing the experiments with friends for a casual “gee whiz” reaction. It should be candidly presented as vibe-coded or AI-coded work rather than as wholly original authorship.

## Phase 1: Collection and publication — complete

Completed work:

1. Published the existing experiments as a simple static website.
2. Added a project landing page that links to every experiment.
3. Hosted the public site with GitHub Pages from the repository's `docs/` directory.
4. Hosted the source in a public GitHub repository.

Two original Phase 1 goals were abandoned because they no longer fit the project's direction:

- Fully refactoring the existing experiments and translating their JavaScript to TypeScript.
- Incrementally cleaning up all existing experiment code, layouts, filenames, and styling.

The existing experiments remain useful artifacts and research tools, but they are not the codebase from which the new design must be mechanically extracted.

## Phase 2: Exploration and core color selection

1. Explore the proposed color-selection concepts alongside relevant prior art, traditional artistic systems, and existing color tools.
2. Refine the design through focused experiments rather than treating the current Paper Doll implementation as the foundation.
3. Implement the resulting core color-selection system as a reusable headless library, independent of any particular frontend or superhero application.

## Phase 3: Consumers

1. Implement `supers_color`, the superhero-specific code layer that consumes the headless color-selection library.
2. Build Paper Doll v2 in this repository as a frontend consumer.
3. Support a Random Superhero Generator as a separate consumer outside this repository.

Paper Doll v2 and the Random Superhero Generator are related consumers, but they are separate applications with different repository boundaries.

## Phase 4: Retrospective

1. Clean up the project documentation.
2. Reflect on the project's process and assess its successes, failures, and lessons.

## Underlying goals

- Compile and organize the experiments for personal reference.
- Explore the transition from systematic color models to intuitive and emotional aesthetic results.
- Develop reusable rules for producing coherent superhero color schemes.
- Support personal TTRPG character-generation projects without making them all part of this repository.
- Make the AI-assisted origin clear and keep the presentation low-ego.
- Make the experiments easy to share with personal friends.
- Preserve the playful, exploratory character of the original work.

## Non-goals

- Presenting the project as résumé material or professional-development work.
- Claiming the generated experiments as wholly original work.
- Making the site highly polished, formal, or product-like.
- Presenting the experiments as pedagogical, academic, or scientific material.
- Adding server-side infrastructure when static hosting is sufficient.
- Fully refactoring or translating every existing experiment into TypeScript.
- Housing the Random Superhero Generator itself in this repository.

## Historical documentation

The files under `agent_docs/deprecated/paper_doll/` describe the old Paper Doll system. They are preserved only as historical records and should not be updated or reconciled with the current project direction.

The `agent_docs/convo_X_work_summary.md` files are likewise records of the conversations in which the documented work and plans occurred. They should not be updated when later decisions supersede their contents; current direction belongs in this document instead.

## Current technical direction

- Static HTML, CSS, and browser JavaScript published from `docs/`.
- New reusable color-selection code should be headless and kept separate from application and DOM concerns.
- `supers_color` should add superhero-specific rules without making those rules part of the general color-selection core.
- Paper Doll v2 belongs in this repository; the Random Superhero Generator does not.
- New code may use TypeScript without requiring the existing experiment JavaScript to be translated or refactored.
- Keep tooling minimal.
- No application framework unless later experiments provide a concrete reason to add one.
