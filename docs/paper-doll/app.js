import { DEFAULT_PALETTE_CONSTANTS, buildPalettes, clamp, fmt, generate_palette, hexToOklch, oklchLabel, oklchToHex, wrapHue } from "./colors.js";
import { buildPaperDollHarmonyHues } from "../assets/harmony.js";
const LAYER_ORDER = ["skin", "main", "support", "accent", "hair", "eyes", "power"];
const PAPER_ROLES = [["main", "Main Costume"], ["support", "Supporting Costume"], ["accent", "Accent / Highlight"], ["hair", "Hair + Eyebrows"], ["eyes", "Eyes"], ["skin", "Skin"], ["power", "Power / Stars"]];
const DOLL_CATALOG = [{ kind: "male", label: "Male" }, { kind: "female", label: "Female" }];
const SCHOOL_UNIFORM_SWATCHES = [
    { label: "Primary", key: "schoolUniformPrimaryHex" },
    { label: "Secondary", key: "schoolUniformSecondaryHex" },
    { label: "Highlight", key: "schoolUniformHighlightHex" }
];
let activeIndex = 0;
let activeDollIndex = 0;
let suppressColorSync = false;
let paletteRecipes = [];
let currentDollPair = { school: {}, full: {} };
// Finds a required DOM element by id and gives callers a typed element back.
const el = (id) => {
    const node = document.getElementById(id);
    if (!node)
        throw new Error(`Missing required element: #${id}`);
    return node;
};
// Reads a numeric input value, falling back when an optional control is absent or invalid.
const readNum = (id, fallback = 0) => { const node = document.getElementById(id); if (!node)
    return fallback; const value = parseFloat(node.value); return Number.isFinite(value) ? value : fallback; };
// Builds browser-relative asset paths while trimming accidental leading/trailing slashes.
const assetPath = (...parts) => `./${parts.map(part => String(part).replace(/^\.?\//, "").replace(/\/$/, "")).filter(Boolean).join("/")}`;
const MASK_ASSETS = {
    female: Object.fromEntries(LAYER_ORDER.map(role => [role, assetPath("female_layers", `${role}.png`)])),
    male: Object.fromEntries(LAYER_ORDER.map(role => [role, assetPath("male_layers", `${role}.png`)]))
};
// Collects all UI control values into the plain data object used by the palette engine.
function readConstants() {
    return {
        baseH: wrapHue(readNum("baseH", DEFAULT_PALETTE_CONSTANTS.baseH)), baseL: clamp(readNum("baseL", DEFAULT_PALETTE_CONSTANTS.baseL), 0, 100), baseC: Math.max(0, readNum("baseC1000", DEFAULT_PALETTE_CONSTANTS.baseC * 1000) / 1000),
        anaOffset: readNum("anaOffset", DEFAULT_PALETTE_CONSTANTS.anaOffset), compOffset: readNum("compOffset", DEFAULT_PALETTE_CONSTANTS.compOffset), rightAngleOffset: readNum("rightAngleOffset", DEFAULT_PALETTE_CONSTANTS.rightAngleOffset), splitOffset: readNum("splitOffset", DEFAULT_PALETTE_CONSTANTS.splitOffset),
        mainLightDelta: readNum("mainLightDelta", DEFAULT_PALETTE_CONSTANTS.mainLightDelta), mainDarkDelta: readNum("mainDarkDelta", DEFAULT_PALETTE_CONSTANTS.mainDarkDelta), mainDesat: readNum("mainDesatPct", DEFAULT_PALETTE_CONSTANTS.mainDesat * 100) / 100,
        supportLightDelta: readNum("supportLightDelta", DEFAULT_PALETTE_CONSTANTS.supportLightDelta), supportDarkDelta: readNum("supportDarkDelta", DEFAULT_PALETTE_CONSTANTS.supportDarkDelta), supportDesat: readNum("supportDesatPct", DEFAULT_PALETTE_CONSTANTS.supportDesat * 100) / 100,
        highlightLightDelta: readNum("highlightLightDelta", DEFAULT_PALETTE_CONSTANTS.highlightLightDelta), highlightDarkDelta: readNum("highlightDarkDelta", DEFAULT_PALETTE_CONSTANTS.highlightDarkDelta), highlightBoost: readNum("highlightBoostPct", DEFAULT_PALETTE_CONSTANTS.highlightBoost * 100) / 100,
        lOffWhiteLight: readNum("lOffWhiteLight", DEFAULT_PALETTE_CONSTANTS.lOffWhiteLight), lOffWhiteDark: readNum("lOffWhiteDark", DEFAULT_PALETTE_CONSTANTS.lOffWhiteDark), cOffWhite: readNum("cOffWhite1000", DEFAULT_PALETTE_CONSTANTS.cOffWhite * 1000) / 1000,
        lOffBlackLight: readNum("lOffBlackLight", DEFAULT_PALETTE_CONSTANTS.lOffBlackLight), lOffBlackDark: readNum("lOffBlackDark", DEFAULT_PALETTE_CONSTANTS.lOffBlackDark), cOffBlack: readNum("cOffBlack1000", DEFAULT_PALETTE_CONSTANTS.cOffBlack * 1000) / 1000,
        lPureWhite: readNum("lPureWhite", DEFAULT_PALETTE_CONSTANTS.lPureWhite), lPureLightGray: readNum("lPureLightGray", DEFAULT_PALETTE_CONSTANTS.lPureLightGray), lPureDarkGray: readNum("lPureDarkGray", DEFAULT_PALETTE_CONSTANTS.lPureDarkGray), lPureBlack: readNum("lPureBlack", DEFAULT_PALETTE_CONSTANTS.lPureBlack),
        skinHex: document.getElementById("skinColor")?.value ?? DEFAULT_PALETTE_CONSTANTS.skinHex,
        schoolUniformPrimaryHex: document.getElementById("schoolUniformPrimaryColor")?.value ?? DEFAULT_PALETTE_CONSTANTS.schoolUniformPrimaryHex,
        schoolUniformSecondaryHex: document.getElementById("schoolUniformSecondaryColor")?.value ?? DEFAULT_PALETTE_CONSTANTS.schoolUniformSecondaryHex,
        schoolUniformHighlightHex: document.getElementById("schoolUniformHighlightColor")?.value ?? DEFAULT_PALETTE_CONSTANTS.schoolUniformHighlightHex
    };
}
// Loads the editable palette recipe data file before the first render.
async function loadPaletteRecipes() { const response = await fetch("./palettes.json"); if (!response.ok)
    throw new Error(`Could not load palettes.json: ${response.status}`); return response.json(); }
// Applies one mask image to an element using both standard and WebKit CSS properties.
function applyMask(node, url) { const value = `url("${url}")`; const style = node.style; style.maskImage = value; style.webkitMaskImage = value; }
// Creates one colored paper-doll layer whose shape comes from a mask image.
function makeLayer(role, url) { const layer = document.createElement("div"); layer.className = "mask-layer"; layer.dataset.role = role; layer.style.backgroundColor = `var(--role-${role})`; applyMask(layer, url); return layer; }
// Clones the HTML template that defines the outer paper-doll element.
function cloneDollTemplate() {
    const template = el("paperDollTemplate");
    const node = template.content.firstElementChild?.cloneNode(true);
    if (!node)
        throw new Error("Paper doll template must contain one div root.");
    node.innerHTML = "";
    return node;
}
// Stacks all body-part mask layers for one reusable paper-doll definition.
function makeFigure(doll) { const stack = cloneDollTemplate(); stack.ariaLabel = doll.label; const assets = MASK_ASSETS[doll.kind]; for (const role of LAYER_ORDER)
    stack.appendChild(makeLayer(role, assets[role])); return stack; }
// Wraps a painted doll with the small comparison label used only by this app's carousel.
function makeDollComparison(label, doll) { const wrap = document.createElement("div"); wrap.className = "doll-comparison"; const caption = document.createElement("div"); caption.className = "doll-comparison-label"; caption.textContent = label; wrap.appendChild(doll); wrap.appendChild(caption); return wrap; }
// Shows the active doll in a small carousel so new doll definitions can be added later.
function renderDollCarousel(dollPair) { const root = el("paperRoot"); const doll = DOLL_CATALOG[activeDollIndex]; if (!doll)
    throw new Error("No paper dolls are available to render."); root.innerHTML = ""; root.appendChild(makeDollComparison("Student Uniform", paintdoll(doll.kind, dollPair.school))); root.appendChild(makeDollComparison("Full Palette", paintdoll(doll.kind, dollPair.full))); el("dollCarouselLabel").textContent = `${doll.label} ${activeDollIndex + 1} of ${DOLL_CATALOG.length}`; }
// Advances the doll carousel, wrapping around at either end.
function moveDollCarousel(delta) { activeDollIndex = (activeDollIndex + delta + DOLL_CATALOG.length) % DOLL_CATALOG.length; renderDollCarousel(currentDollPair); }
// Writes the active doll colors into CSS custom properties used by the mask layers.
function applyDollPalette(node, doll) { for (const [role] of PAPER_ROLES)
    node.style.setProperty(`--role-${role}`, doll[role] ?? "transparent"); }
// Public helper: create one painted doll element without mounting it into the app carousel.
export function paintdoll(dolltype, palette) {
    const doll = DOLL_CATALOG.find(item => item.kind === dolltype);
    if (!doll)
        throw new Error(`Unknown paper doll type: ${dolltype}`);
    const figure = makeFigure(doll);
    applyDollPalette(figure, "doll" in palette ? palette.doll : palette);
    return figure;
}
export { generate_palette, generate_palette as generatePalette, paintdoll as paintDoll };
// Renders the clickable palette tiles and wires each tile to activate its palette.
function renderPaletteButtons(palettes) { const root = el("paletteButtons"); root.innerHTML = ""; palettes.forEach((palette, index) => { const button = document.createElement("button"); button.type = "button"; button.className = "palette-button" + (index === activeIndex ? " active" : ""); button.dataset.index = String(index); const miniRoles = ["main", "support", "accent", "hair", "eyes", "power"]; const mini = miniRoles.map(role => `<span class="mini-swatch" title="${role} ${palette.doll[role] ?? "transparent"}" style="background:${palette.doll[role] ?? "transparent"}"></span>`).join(""); button.innerHTML = `<div class="palette-button-title">${index + 1}. ${palette.name}</div><div class="mini-swatches">${mini}</div>`; button.addEventListener("click", () => { activeIndex = index; render(); }); root.appendChild(button); }); }
// Shows the active palette's important role mapping and every generated swatch.
function renderSwatches(palette) { const root = el("swatchList"); root.innerHTML = ""; const map = document.createElement("div"); map.className = "role-map-summary"; const roleNames = { costumePrimary: "Costume Primary", costumeSecondary: "Costume Secondary", costumeAccent: "Costume Accent", hair: "Hair", eyes: "Eyes", power: "Power" }; map.innerHTML = Object.entries(roleNames).map(([key, label]) => { const imp = palette.important[key]; const chipBg = imp?.hex === "transparent" ? "transparent" : imp?.hex; return `<div class="paper-role"><span class="chip" style="background:${chipBg}"></span><span><strong>${label}</strong><code>${imp?.label ?? "N/A"} ${imp?.hex ?? "transparent"}</code></span></div>`; }).join(""); root.appendChild(map); for (const c of palette.colors) {
    const row = document.createElement("div");
    row.className = "swatch-row";
    row.innerHTML = `<div class="swatch" style="background:${c.hex}"></div><div><div class="swatch-title">${c.role} — ${c.label}</div><div class="swatch-meta">${oklchLabel(c)} · HEX ${c.hex}</div><div class="pill-row"><span class="pill">${c.group}</span><span class="pill">${c.variant}</span></div></div>`;
    root.appendChild(row);
} }
// Lists the exact paper-doll role colors currently applied to the figure preview.
function renderPaperRoles(doll) { const root = el("paperRoles"); root.innerHTML = ""; for (const [role, label] of PAPER_ROLES) {
    const value = doll[role] ?? "transparent";
    const row = document.createElement("div");
    row.className = "paper-role";
    row.innerHTML = `<span class="chip" style="background:${value}"></span><span><strong>${label}</strong><code>${role} ${value}</code></span>`;
    root.appendChild(row);
} }
// Shows the fixed school-uniform colors as read-only reference swatches.
function renderSchoolUniformReference(k) { const root = el("schoolUniformReference"); root.innerHTML = SCHOOL_UNIFORM_SWATCHES.map(color => { const hex = k[color.key]; return `<div class="paper-role"><span class="chip" style="background:${hex}"></span><span><strong>${color.label}</strong><code>${hex}</code></span></div>`; }).join(""); }
// Builds the copyable text report for the currently selected palette.
function paletteText(palette, k) { const hues = buildPaperDollHarmonyHues(k.baseH, k); const lines = []; lines.push(palette.name.toUpperCase()); lines.push(palette.note); lines.push(""); lines.push(`BASE: OKLCH H ${fmt(k.baseH)} L ${fmt(k.baseL)} C ${fmt(k.baseC, 4)} HEX ${oklchToHex(k.baseL, k.baseC, k.baseH)}`); lines.push(`ANALOG 1: H ${fmt(hues.analog1)}`); lines.push(`ANALOG 2: H ${fmt(hues.analog2)}`); lines.push(`COMPLEMENT: H ${fmt(hues.complement)}`); lines.push(`RIGHT ANGLE 1: H ${fmt(hues.rightAngle1)}`); lines.push(`RIGHT ANGLE 2: H ${fmt(hues.rightAngle2)}`); lines.push(`SPLIT COMPLEMENT 1: H ${fmt(hues.splitComplement1)}`); lines.push(`SPLIT COMPLEMENT 2: H ${fmt(hues.splitComplement2)}`); lines.push(""); lines.push("ROLE MAPPING"); const roleNames = { costumePrimary: "Costume Primary", costumeSecondary: "Costume Secondary", costumeAccent: "Costume Accent", hair: "Hair", eyes: "Eyes", power: "Power" }; for (const [key, label] of Object.entries(roleNames)) {
    const imp = palette.important[key];
    lines.push(`${label}: ${imp?.label ?? "N/A"}`);
} lines.push(""); lines.push("COMPLETE PALETTE"); for (const c of palette.colors)
    lines.push(`${c.role}: ${oklchLabel(c)} HEX ${c.hex}`); lines.push(""); lines.push("PAPER DOLL PALETTE"); for (const [role, label] of PAPER_ROLES)
    lines.push(`${role}: ${palette.doll[role] ?? "transparent"} (${label})`); return lines.join("\n"); }
// Recomputes palettes from the controls and refreshes every dependent UI panel.
function render(syncBaseColor = true) { const k = readConstants(); if (syncBaseColor && !suppressColorSync)
    el("baseColor").value = oklchToHex(k.baseL, k.baseC, k.baseH); const palettes = buildPalettes(k, paletteRecipes); const schoolPalettes = buildPalettes(k, paletteRecipes, { schoolUniformOverride: true }); activeIndex = clamp(activeIndex, 0, palettes.length - 1); const active = palettes[activeIndex]; const schoolActive = schoolPalettes[activeIndex]; if (!active || !schoolActive)
    throw new Error("No palettes are available to render."); currentDollPair = { school: schoolActive.doll, full: active.doll }; renderPaletteButtons(palettes); el("activeTitle").textContent = `${activeIndex + 1}. ${active.name}`; el("activeNote").textContent = active.note; renderSchoolUniformReference(k); renderDollCarousel(currentDollPair); renderPaperRoles(active.doll); renderSwatches(active); el("activeOutput").value = paletteText(active, k); }
// Converts the color picker value back into OKLCH controls before rendering.
function syncBaseFromColorPicker() { suppressColorSync = true; const o = hexToOklch(el("baseColor").value); el("baseH").value = String(Math.round(o.H)); el("baseL").value = String(Math.round(o.L100)); el("baseC1000").value = String(Math.round(o.C * 1000)); suppressColorSync = false; render(false); }
function wireAppEvents() {
    el("baseColor").addEventListener("input", syncBaseFromColorPicker);
    // Re-renders when typed OKLCH base controls change.
    for (const id of ["baseH", "baseL", "baseC1000"])
        el(id).addEventListener("input", () => render(true));
    // Re-renders when any derived palette adjustment control changes.
    for (const node of document.querySelectorAll("[data-render]"))
        node.addEventListener("input", () => render(true));
    // Copies the active palette report, falling back to selection-based copy when needed.
    el("copyActive").addEventListener("click", async () => { const output = el("activeOutput"); const text = output.value; try {
        await navigator.clipboard.writeText(text);
    }
    catch {
        output.select();
        document.execCommand("copy");
    } });
    el("prevDoll").addEventListener("click", () => moveDollCarousel(-1));
    el("nextDoll").addEventListener("click", () => moveDollCarousel(1));
}
// Loads data, creates the static preview DOM, and performs the first render.
async function init() { wireAppEvents(); paletteRecipes = await loadPaletteRecipes(); render(true); }
if (typeof document !== "undefined" && document.getElementById("paperRoot"))
    void init();
