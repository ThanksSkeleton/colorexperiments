import {
    GAMUT_MAPPING_METHODS,
    hexToOklch as sharedHexToOklch,
    oklchToHex as sharedOklchToHex
} from "../assets/colors.js";
import {
    buildPaperDollHarmonyHues,
    PAPER_DOLL_HARMONY_DEFAULTS
} from "../assets/harmony.js";

export const DEFAULT_PALETTE_CONSTANTS = {
    baseH: 253, baseL: 62, baseC: 0.18,
    ...PAPER_DOLL_HARMONY_DEFAULTS,
    mainLightDelta: 18, mainDarkDelta: 18, mainDesat: 0.75,
    supportLightDelta: 18, supportDarkDelta: 18, supportDesat: 0.75,
    highlightLightDelta: 18, highlightDarkDelta: 18, highlightBoost: 1.25,
    lOffWhiteLight: 94, lOffWhiteDark: 82, cOffWhite: 0.05,
    lOffBlackLight: 32, lOffBlackDark: 14, cOffBlack: 0.025,
    lPureWhite: 98, lPureLightGray: 76, lPureDarkGray: 42, lPureBlack: 8,
    skinHex: "#d9a066",
    schoolUniformPrimaryHex: "#dadae1",
    schoolUniformSecondaryHex: "#008080",
    schoolUniformHighlightHex: "#e50000"
};
const SCHOOL_UNIFORM_COLORS = [
    { roleKey: "costumePrimary", layer: "main", label: "School Uniform Primary", role: "costume_primary", hexKey: "schoolUniformPrimaryHex" },
    { roleKey: "costumeSecondary", layer: "support", label: "School Uniform Secondary", role: "costume_secondary", hexKey: "schoolUniformSecondaryHex" },
    { roleKey: "costumeAccent", layer: "accent", label: "School Uniform Highlight", role: "costume_accent", hexKey: "schoolUniformHighlightHex" }
];
// Keeps a number inside a closed range, usually for color channels or OKLCH lightness.
export const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
// Normalizes any hue angle into the browser-friendly 0-360 degree range.
export const wrapHue = (h) => ((Number(h) % 360) + 360) % 360;
// Formats numeric color values for compact display in labels and reports.
export const fmt = (value, digits = 2) => Number(value).toFixed(digits).replace(/\.?0+$/, "");
// Converts an OKLCH color into clipped sRGB hex for browser display.
export function oklchToHex(L100, C, H) {
    return sharedOklchToHex(
        { L: clamp(L100, 0, 100) / 100, C: Math.max(0, C), h: wrapHue(H) },
        { method: GAMUT_MAPPING_METHODS.REDUCE_CHROMA }
    );
}
// Converts a browser hex color back into OKLCH controls for editing.
export function hexToOklch(hex) {
    const { L, C, h } = sharedHexToOklch(hex);
    return { L100: L * 100, C, H: h };
}
// Produces the human-readable OKLCH label used in swatch rows and text output.
export function oklchLabel(c) { return c.h === null ? `OKLCH H none L ${fmt(c.l)} C ${fmt(c.c, 4)}` : `OKLCH H ${fmt(c.h)} L ${fmt(c.l)} C ${fmt(c.c, 4)}`; }
// Creates a normalized palette color object and computes its display hex value.
function makeColor(label, role, group, variant, h, l, c) {
    const L = clamp(l, 0, 100);
    const C = Math.max(0, c);
    const H = h === null ? null : wrapHue(h);
    return { label, role, group, variant, h: H, l: L, c: C, hex: oklchToHex(L, C, H ?? 0) };
}
// Creates a swatch entry from a fixed sRGB color while still recording its OKLCH coordinates.
function makeFixedColor(label, role, group, variant, hex) {
    const o = hexToOklch(hex);
    return { label, role, group, variant, h: o.H, l: o.L100, c: o.C, hex };
}
// Creates important-role metadata from a fixed sRGB color.
function makeFixedImportant(label, hex) {
    const o = hexToOklch(hex);
    return { kind: "N/A", label, h: o.H, l: o.L100, c: o.C, hex };
}
// Builds all palette variants from UI constants and structured recipe data.
export function buildPalettes(k, recipes, options = {}) {
    const H = k.baseH, L = k.baseL, C = k.baseC;
    const hues = buildPaperDollHarmonyHues(H, k);
    const labels = {
        input: "Input",
        inputDesat: "Input Desat",
        inputDesatDark: "Input Desat Dark",
        analog1: "Analog 1",
        analog2: "Analog 2",
        complement: "Complement",
        rightAngle1: "Right Angle 1",
        rightAngle2: "Right Angle 2",
        splitComplement1: "Split Complement 1",
        splitComplement2: "Split Complement 2",
        white: "White",
        black: "Black",
        primary: "Primary"
    };
    const roleSpecs = {
        costumePrimary: { layer: "main", label: "Costume Primary", role: "costume_primary", group: "Costume Primary", lightDelta: k.mainLightDelta, darkDelta: k.mainDarkDelta, desat: k.mainDesat },
        costumeSecondary: { layer: "support", label: "Costume Secondary", role: "costume_secondary", group: "Costume Secondary", lightDelta: k.supportLightDelta, darkDelta: k.supportDarkDelta, desat: k.supportDesat },
        costumeAccent: { layer: "accent", label: "Costume Accent", role: "costume_accent", group: "Costume Accent", lightDelta: k.highlightLightDelta, darkDelta: k.highlightDarkDelta, desat: k.highlightBoost },
        hair: { layer: "hair", label: "Hair", role: "hair", group: "Hair", lightDelta: Math.round(k.supportLightDelta / 2), darkDelta: Math.round(k.supportDarkDelta / 2), desat: k.supportDesat },
        eyes: { layer: "eyes", label: "Eyes", role: "eyes", group: "Eyes", lightDelta: 0, darkDelta: 0, desat: 1 },
        power: { layer: "power", label: "Power", role: "power", group: "Power", lightDelta: k.highlightLightDelta, darkDelta: k.highlightDarkDelta, desat: k.highlightBoost }
    };
    // Resolves a recipe color kind into the key color assigned to one paper-doll role.
    function importantColor(kind, roleKey) {
        if (kind === "N/A")
            return { kind, label: "N/A", hex: "transparent", h: null, l: null, c: null };
        if (kind === "primary")
            kind = "input";
        if (kind === "white")
            return { kind, label: labels.white, h: null, l: k.lPureWhite, c: 0, hex: oklchToHex(k.lPureWhite, 0, 0) };
        if (kind === "black")
            return { kind, label: labels.black, h: null, l: k.lPureBlack, c: 0, hex: oklchToHex(k.lPureBlack, 0, 0) };
        if (kind === "inputDesat")
            return { kind, label: labels.inputDesat, h: H, l: k.lOffWhiteLight, c: k.cOffWhite, hex: oklchToHex(k.lOffWhiteLight, k.cOffWhite, H) };
        if (kind === "inputDesatDark")
            return { kind, label: labels.inputDesatDark, h: H, l: k.lOffBlackLight, c: k.cOffBlack, hex: oklchToHex(k.lOffBlackLight, k.cOffBlack, H) };
        const h = hues[kind];
        const chroma = roleKey === "costumeAccent" || roleKey === "power" ? C * k.highlightBoost : C;
        return { kind, label: labels[kind], h, l: L, c: chroma, hex: oklchToHex(L, chroma, h ?? 0) };
    }
    // Derives a concrete swatch from an important role color with adjusted lightness and chroma.
    function colorFromImportant(name, role, variant, important, l, c) {
        const h = important.h === null ? null : important.h;
        return makeColor(`${name} ${variant}`, role, name, variant, h, l, c);
    }
    // Expands one role assignment into its base, light, and dark swatch package.
    function packageFor(roleKey, kind) {
        if (kind === "N/A")
            return [];
        const spec = roleSpecs[roleKey];
        const important = importantColor(kind, roleKey);
        if (important.l === null || important.c === null)
            return [];
        if (roleKey === "eyes")
            return [colorFromImportant(spec.label, spec.role, important.label, important, important.l, important.c)];
        if (roleKey === "power") {
            return [
                colorFromImportant(spec.label, spec.role, important.label, important, important.l, important.c),
                colorFromImportant(spec.label, `${spec.role}_light`, `${important.label} Light`, important, important.l + spec.lightDelta, important.c),
                colorFromImportant(spec.label, `${spec.role}_dark`, `${important.label} Dark`, important, important.l - spec.darkDelta, important.c)
            ];
        }
        return [
            colorFromImportant(spec.label, spec.role, important.label, important, important.l, important.c),
            colorFromImportant(spec.label, `${spec.role}_light`, `${important.label} Light`, important, important.l + spec.lightDelta, important.c * spec.desat),
            colorFromImportant(spec.label, `${spec.role}_dark`, `${important.label} Dark`, important, important.l - spec.darkDelta, important.c * spec.desat)
        ];
    }
    // Builds one complete palette, including role metadata, swatches, and preview colors.
    function buildPalette(name, note, roleMap) {
        const orderedRoles = ["costumePrimary", "costumeSecondary", "costumeAccent", "hair", "eyes", "power"];
        const colors = [];
        const important = {};
        const doll = { skin: k.skinHex };
        for (const roleKey of orderedRoles) {
            const kind = roleMap[roleKey];
            const spec = roleSpecs[roleKey];
            if (kind === "N/A") {
                important[roleKey] = { kind, label: "N/A", hex: "transparent", h: null, l: null, c: null };
                doll[spec.layer] = "transparent";
                continue;
            }
            important[roleKey] = importantColor(kind, roleKey);
            doll[spec.layer] = important[roleKey].hex;
            colors.push(...packageFor(roleKey, kind));
        }
        if (options.schoolUniformOverride) {
            const costumeRolePrefixes = SCHOOL_UNIFORM_COLORS.map(color => color.role);
            for (let i = colors.length - 1; i >= 0; i--) {
                if (costumeRolePrefixes.some(role => colors[i].role === role || colors[i].role.startsWith(`${role}_`)))
                    colors.splice(i, 1);
            }
            for (const color of SCHOOL_UNIFORM_COLORS) {
                const hex = k[color.hexKey];
                important[color.roleKey] = makeFixedImportant(color.label, hex);
                doll[color.layer] = hex;
                colors.push(makeFixedColor(color.label, color.role, "School Uniform", "Fixed", hex));
            }
            return { name: `${name} School Uniform`, family: name, note: `${note} Costume colors are using the school uniform override.`, roleMap, important, colors, doll };
        }
        return { name, family: name, note, roleMap, important, colors, doll };
    }
    return recipes.map(recipe => buildPalette(recipe.name, recipe.note, recipe.roleMap));
}
// Public helper: build the available palettes from a single browser hex color.
export function generate_palette(inputColor, recipes, options = {}, constants = DEFAULT_PALETTE_CONSTANTS) {
    const base = hexToOklch(inputColor);
    return buildPalettes({ ...constants, baseH: base.H, baseL: base.L100, baseC: base.C }, recipes, options);
}
export { generate_palette as generatePalette };
