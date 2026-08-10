/**
 * Pure color-space conversions used by the browser experiments.
 *
 * Conventions:
 * - sRGB and linear-sRGB channels are normalized to 0..1.
 * - HSV saturation and value are normalized to 0..1.
 * - OKLab and OKLCH lightness is normalized to 0..1.
 * - OKLCH hue is expressed in degrees and normalized to 0..<360.
 * - Conversion functions do not silently gamut-map. Call
 *   `mapOklchToSrgb()` when an in-gamut display color is required.
 */

const SRGB_EPSILON = 1e-7;

/** Restrict a number to a closed interval. */
export function clamp(value, min = 0, max = 1) {
  return Math.min(max, Math.max(min, value));
}

/** Normalize an angle in degrees to the interval 0..<360. */
export function normalizeHue(hue) {
  return ((Number(hue) % 360) + 360) % 360;
}

/** Convert HSV to normalized gamma-encoded sRGB. */
export function hsvToSrgb({ h, s, v }) {
  const hue = normalizeHue(h);
  const chroma = v * s;
  const hueSector = hue / 60;
  const intermediate = chroma * (1 - Math.abs((hueSector % 2) - 1));
  let r = 0;
  let g = 0;
  let b = 0;

  if (hueSector < 1) [r, g, b] = [chroma, intermediate, 0];
  else if (hueSector < 2) [r, g, b] = [intermediate, chroma, 0];
  else if (hueSector < 3) [r, g, b] = [0, chroma, intermediate];
  else if (hueSector < 4) [r, g, b] = [0, intermediate, chroma];
  else if (hueSector < 5) [r, g, b] = [intermediate, 0, chroma];
  else [r, g, b] = [chroma, 0, intermediate];

  const minimum = v - chroma;
  return { r: r + minimum, g: g + minimum, b: b + minimum };
}

/**
 * Convert normalized gamma-encoded sRGB to HSV.
 * Achromatic colors have no intrinsic hue, so this function represents it as 0.
 */
export function srgbToHsv({ r, g, b }) {
  const maximum = Math.max(r, g, b);
  const minimum = Math.min(r, g, b);
  const chroma = maximum - minimum;
  let h = 0;

  if (chroma !== 0) {
    if (maximum === r) h = 60 * (((g - b) / chroma) % 6);
    else if (maximum === g) h = 60 * ((b - r) / chroma + 2);
    else h = 60 * ((r - g) / chroma + 4);
  }

  return {
    h: normalizeHue(h),
    s: maximum === 0 ? 0 : chroma / maximum,
    v: maximum,
  };
}

/** Decode one gamma-encoded sRGB channel into linear light. */
export function srgbChannelToLinear(channel) {
  return channel <= 0.04045
    ? channel / 12.92
    : ((channel + 0.055) / 1.055) ** 2.4;
}

/** Encode one linear-light channel as gamma-encoded sRGB. */
export function linearChannelToSrgb(channel) {
  return channel <= 0.0031308
    ? 12.92 * channel
    : 1.055 * channel ** (1 / 2.4) - 0.055;
}

/** Convert normalized gamma-encoded sRGB to linear sRGB. */
export function srgbToLinear({ r, g, b }) {
  return {
    r: srgbChannelToLinear(r),
    g: srgbChannelToLinear(g),
    b: srgbChannelToLinear(b),
  };
}

/** Convert linear sRGB to normalized gamma-encoded sRGB. */
export function linearToSrgb({ r, g, b }) {
  return {
    r: linearChannelToSrgb(r),
    g: linearChannelToSrgb(g),
    b: linearChannelToSrgb(b),
  };
}

/** Convert linear sRGB to OKLab using the published OKLab matrices. */
export function linearSrgbToOklab({ r, g, b }) {
  const l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b;
  const m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b;
  const s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b;
  const lRoot = Math.cbrt(l);
  const mRoot = Math.cbrt(m);
  const sRoot = Math.cbrt(s);

  return {
    L: 0.2104542553 * lRoot + 0.793617785 * mRoot - 0.0040720468 * sRoot,
    a: 1.9779984951 * lRoot - 2.428592205 * mRoot + 0.4505937099 * sRoot,
    b: 0.0259040371 * lRoot + 0.7827717662 * mRoot - 0.808675766 * sRoot,
  };
}

/** Convert OKLab to linear sRGB. Values may lie outside the sRGB gamut. */
export function oklabToLinearSrgb({ L, a, b }) {
  const lRoot = L + 0.3963377774 * a + 0.2158037573 * b;
  const mRoot = L - 0.1055613458 * a - 0.0638541728 * b;
  const sRoot = L - 0.0894841775 * a - 1.291485548 * b;
  const l = lRoot ** 3;
  const m = mRoot ** 3;
  const s = sRoot ** 3;

  return {
    r: 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    g: -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    b: -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  };
}

/** Convert OKLab Cartesian coordinates to cylindrical OKLCH coordinates. */
export function oklabToOklch({ L, a, b }) {
  const C = Math.hypot(a, b);
  return { L, C, h: C < Number.EPSILON ? 0 : normalizeHue(Math.atan2(b, a) * 180 / Math.PI) };
}

/** Convert cylindrical OKLCH coordinates to OKLab. */
export function oklchToOklab({ L, C, h }) {
  const radians = normalizeHue(h) * Math.PI / 180;
  return { L, a: C * Math.cos(radians), b: C * Math.sin(radians) };
}

/** Convert gamma-encoded sRGB directly to OKLab. */
export function srgbToOklab(rgb) {
  return linearSrgbToOklab(srgbToLinear(rgb));
}

/** Convert OKLab directly to gamma-encoded sRGB without gamut mapping. */
export function oklabToSrgb(lab) {
  return linearToSrgb(oklabToLinearSrgb(lab));
}

/** Convert gamma-encoded sRGB directly to OKLCH. */
export function srgbToOklch(rgb) {
  return oklabToOklch(srgbToOklab(rgb));
}

/** Convert OKLCH directly to gamma-encoded sRGB without gamut mapping. */
export function oklchToSrgb(lch) {
  return oklabToSrgb(oklchToOklab(lch));
}

/** Return whether all three linear-sRGB channels are inside the display gamut. */
export function isLinearSrgbInGamut({ r, g, b }, epsilon = SRGB_EPSILON) {
  return r >= -epsilon && r <= 1 + epsilon
    && g >= -epsilon && g <= 1 + epsilon
    && b >= -epsilon && b <= 1 + epsilon;
}

/** Return whether an OKLCH color converts into the sRGB gamut. */
export function isOklchInSrgbGamut(lch, epsilon = SRGB_EPSILON) {
  return isLinearSrgbInGamut(oklabToLinearSrgb(oklchToOklab(lch)), epsilon);
}

/**
 * Map OKLCH into sRGB by reducing chroma while preserving lightness and hue.
 *
 * The binary search returns both the requested and mapped colors so callers can
 * disclose gamut mapping in their UI. `iterations` controls search precision.
 */
export function mapOklchToSrgb(requested, iterations = 36) {
  const normalized = {
    L: requested.L,
    C: Math.max(0, requested.C),
    h: normalizeHue(requested.h),
  };
  const requestedLinear = oklabToLinearSrgb(oklchToOklab(normalized));

  let mapped = normalized;
  let wasMapped = !isLinearSrgbInGamut(requestedLinear);

  if (wasMapped) {
    let low = 0;
    let high = normalized.C;
    for (let i = 0; i < iterations; i += 1) {
      const C = (low + high) / 2;
      const candidate = { ...normalized, C };
      if (isOklchInSrgbGamut(candidate)) low = C;
      else high = C;
    }
    mapped = { ...normalized, C: low };
  }

  const mappedLinear = oklabToLinearSrgb(oklchToOklab(mapped));
  const srgb = linearToSrgb({
    r: clamp(mappedLinear.r),
    g: clamp(mappedLinear.g),
    b: clamp(mappedLinear.b),
  });

  return { requested: normalized, mapped, srgb, wasMapped };
}

/** Parse #RGB or #RRGGBB into normalized gamma-encoded sRGB. */
export function hexToSrgb(hex) {
  const match = /^#?([\da-f]{3}|[\da-f]{6})$/i.exec(String(hex).trim());
  if (!match) throw new TypeError(`Invalid hex color: ${hex}`);
  const digits = match[1].length === 3
    ? [...match[1]].map((digit) => digit + digit).join("")
    : match[1];
  return {
    r: Number.parseInt(digits.slice(0, 2), 16) / 255,
    g: Number.parseInt(digits.slice(2, 4), 16) / 255,
    b: Number.parseInt(digits.slice(4, 6), 16) / 255,
  };
}

/** Serialize normalized gamma-encoded sRGB as a clipped #RRGGBB value. */
export function srgbToHex({ r, g, b }) {
  const byte = (channel) => Math.round(clamp(channel) * 255).toString(16).padStart(2, "0");
  return `#${byte(r)}${byte(g)}${byte(b)}`;
}

/** Convert a display-mapped OKLCH color directly to #RRGGBB. */
export function oklchToHex(lch) {
  return srgbToHex(mapOklchToSrgb(lch).srgb);
}

/** Convert #RGB or #RRGGBB directly to OKLCH. */
export function hexToOklch(hex) {
  return srgbToOklch(hexToSrgb(hex));
}
