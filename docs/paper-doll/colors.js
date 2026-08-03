export const DEFAULT_PALETTE_CONSTANTS = {
    baseH: 253, baseL: 62, baseC: 0.18,
    anaOffset: 30, compOffset: 180, rightAngleOffset: 90, splitOffset: 30,
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
// Converts an 8-bit sRGB channel into linear light for color-space math.
function srgbToLinear(v) { v = v / 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }
// Converts a linear-light channel back into an 8-bit sRGB channel.
function linearToSrgb(v) { v = clamp(v, 0, 1); return Math.round(255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055)); }
// Parses a six-digit hex color string into separate sRGB channels.
function hexToRgb(hex) { const clean = hex.replace("#", ""); return { r: parseInt(clean.slice(0, 2), 16), g: parseInt(clean.slice(2, 4), 16), b: parseInt(clean.slice(4, 6), 16) }; }
// Serializes sRGB channels into a clipped six-digit hex color string.
function rgbToHex(r, g, b) { return "#" + [r, g, b].map(x => clamp(Math.round(x), 0, 255).toString(16).padStart(2, "0")).join(""); }
// Converts an OKLCH color into clipped sRGB hex for browser display.
export function oklchToHex(L100, C, H) {
    const L = clamp(L100, 0, 100) / 100;
    const hRad = wrapHue(H) * Math.PI / 180;
    const a = C * Math.cos(hRad);
    const b = C * Math.sin(hRad);
    const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
    const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
    const s_ = L - 0.0894841775 * a - 1.2914855480 * b;
    const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;
    const rLin = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
    const gLin = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
    const bLin = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s;
    return rgbToHex(linearToSrgb(rLin), linearToSrgb(gLin), linearToSrgb(bLin));
}
// Converts a browser hex color back into OKLCH controls for editing.
export function hexToOklch(hex) {
    const { r, g, b } = hexToRgb(hex);
    const R = srgbToLinear(r), G = srgbToLinear(g), B = srgbToLinear(b);
    const l = 0.4122214708 * R + 0.5363325363 * G + 0.0514459929 * B;
    const m = 0.2119034982 * R + 0.6806995451 * G + 0.1073969566 * B;
    const s = 0.0883024619 * R + 0.2817188376 * G + 0.6299787005 * B;
    const l_ = Math.cbrt(l), m_ = Math.cbrt(m), s_ = Math.cbrt(s);
    const L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_;
    const a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_;
    const bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_;
    const C = Math.sqrt(a * a + bb * bb);
    const H = C < 0.00001 ? 0 : wrapHue(Math.atan2(bb, a) * 180 / Math.PI);
    return { L100: L * 100, C, H };
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
    const hues = {
        input: H,
        inputDesat: H,
        inputDesatDark: H,
        analog1: wrapHue(H - k.anaOffset),
        analog2: wrapHue(H + k.anaOffset),
        complement: wrapHue(H + k.compOffset),
        rightAngle1: wrapHue(H + k.rightAngleOffset),
        rightAngle2: wrapHue(H - k.rightAngleOffset),
        splitComplement1: wrapHue(H + k.compOffset - k.splitOffset),
        splitComplement2: wrapHue(H + k.compOffset + k.splitOffset),
        white: null,
        black: null,
        primary: H
    };
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
