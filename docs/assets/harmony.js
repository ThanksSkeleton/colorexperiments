import { normalizeHue } from "./colors.js";

/**
 * Harmony definitions currently used by the Harmony Inspector.
 *
 * These intentionally remain distinct from the Paper Doll definitions below:
 * the Inspector is the more sophisticated harmony model, but the experiments
 * do not yet agree on every angle or named harmony.
 */
export const HARMONY_INSPECTOR_COLOR_SPECS = Object.freeze([
  { key: "base", label: "Base", offset: 0 },
  { key: "analogLeft", label: "Analog -45", offset: -45 },
  { key: "analogRight", label: "Analog +45", offset: 45 },
  { key: "rightLeft", label: "Right -90", offset: -90 },
  { key: "rightRight", label: "Right +90", offset: 90 },
  { key: "triadLeft", label: "Triad -120", offset: -120 },
  { key: "triadRight", label: "Triad +120", offset: 120 },
  { key: "complement", label: "Complement", offset: 180 },
  { key: "splitLeft", label: "Split +157.5", offset: 157.5 },
  { key: "splitRight", label: "Split +202.5", offset: 202.5 },
]);

export const HARMONY_INSPECTOR_HARMONY_SPECS = Object.freeze([
  { key: "primal", label: "Primal", members: ["base", "complement"] },
  { key: "bacLeft", label: "BAC Left", members: ["base", "analogLeft", "complement"] },
  { key: "bacRight", label: "BAC Right", members: ["base", "analogRight", "complement"] },
  { key: "baac", label: "BAAC", members: ["base", "analogLeft", "analogRight", "complement"] },
  { key: "square", label: "Square", members: ["base", "rightLeft", "complement", "rightRight"] },
  { key: "split", label: "Split Complement", members: ["base", "splitLeft", "splitRight"] },
  { key: "triad", label: "Triad", members: ["base", "triadLeft", "triadRight"] },
]);

/** Generate the Inspector's named hue candidates around an input hue. */
export function buildHarmonyInspectorHues(inputHue) {
  return HARMONY_INSPECTOR_COLOR_SPECS.map(spec => ({
    ...spec,
    h: normalizeHue(inputHue + spec.offset),
  }));
}

/**
 * Hue-geometry defaults currently used by the original Paper Doll.
 * These are kept separate until Paper Doll adopts the Inspector's model.
 */
export const PAPER_DOLL_HARMONY_DEFAULTS = Object.freeze({
  anaOffset: 30,
  compOffset: 180,
  rightAngleOffset: 90,
  splitOffset: 30,
});

/** Generate the original Paper Doll's named chromatic hue candidates. */
export function buildPaperDollHarmonyHues(inputHue, geometry = PAPER_DOLL_HARMONY_DEFAULTS) {
  const H = normalizeHue(inputHue);
  return {
    input: H,
    analog1: normalizeHue(H - geometry.anaOffset),
    analog2: normalizeHue(H + geometry.anaOffset),
    complement: normalizeHue(H + geometry.compOffset),
    rightAngle1: normalizeHue(H + geometry.rightAngleOffset),
    rightAngle2: normalizeHue(H - geometry.rightAngleOffset),
    splitComplement1: normalizeHue(H + geometry.compOffset - geometry.splitOffset),
    splitComplement2: normalizeHue(H + geometry.compOffset + geometry.splitOffset),
    // Compatibility alias used by existing Paper Doll recipes.
    primary: H,
  };
}
