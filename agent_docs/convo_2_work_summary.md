# Conversation 2 Work Summary

## Project instructions

- Added a root `AGENTS.md` directing agents to read `agent_docs/project_goals.md` before working.
- Prohibited multimodal LLM image inspection unless the user explicitly overrides the rule for a specific task.
- Kept programmatic image inspection, metadata analysis, and deterministic image-processing tools available when useful.
- Directed agents to defer testing and visual review at the project's current scope and pass changed pages to the user for examination instead.

## Paper Doll archive review

Reviewed the local `input/PaperDollMigration.zip` archive and identified the small set of browser-runtime files needed to publish the experiment independently of its former repository.

The migration intentionally excluded the former repository's development infrastructure, including dependencies, package files, TypeScript sources and configuration, tests, local server helpers, logs, and obsolete assets. No JavaScript cleanup, TypeScript conversion, refactoring, or shared-module integration was performed.

## Paper Doll migration

- Added the Superhero Palette Paper Doll Generator under `docs/paper-doll/`.
- Preserved its runtime HTML, JavaScript, palette data, and male/female image layers without functional changes.
- Preserved the experiment's original relative file layout so its scripts, JSON data, and image references continue to resolve together.
- Added a “Larger experiments” section to `docs/index.html` linking to `./paper-doll/`.
- Archived the former Paper Doll documentation under `agent_docs/deprecated/paper_doll/`.
- Cleaned up the archived documentation before inclusion, retaining concise project goals, terminology, historical activities, palette requirements, and known issues.

Per the root project instructions, the migrated page was handed to the user without agent-run testing or visual inspection.

## Pixel-art attribution

Added the following linked attribution at the bottom of both pixel-role experiments:

> Pixel art from https://ranju.itch.io/high-school-students-portraits-pack

Updated pages:

- `docs/heuristic_role_hue_map_prototype.html`
- `docs/angelo_role_review_prototype_v5.html`

## Current Paper Doll layout

```text
docs/paper-doll/
  index.html
  app.js
  colors.js
  palettes.json
  female_layers/
  male_layers/

agent_docs/deprecated/paper_doll/
  Goals.md
  Goals2.md
  definitions.md
  handoff01.md
  handoff02.md
  handoff03.md
  known_issues.md
  palette_requirements.md
```
