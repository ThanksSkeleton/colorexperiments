# Historical Activity: Code and Data Separation

The standalone prototype was separated into a small browser application:

- `index.html` retained page markup and CSS.
- `app.ts` handled UI wiring, rendering, paper-doll previews, and palette output.
- `colors.ts` handled color conversion, palette construction, and color helpers.
- `palettes.json` stored structured palette recipes.
- Compiled `app.js` and `colors.js` supplied the browser runtime.

An encoding check was also introduced and used to repair visible text-encoding artifacts. Comments were added to the TypeScript helpers to describe their roles.

This build structure belonged to the former standalone repository. The migrated static experiment retains only the files required by its browser runtime.
