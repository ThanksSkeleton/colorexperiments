import assert from "node:assert/strict";
import test from "node:test";

import {
  hexToOklch,
  hexToSrgb,
  hsvToSrgb,
  isOklchInSrgbGamut,
  linearToSrgb,
  mapOklchToSrgb,
  normalizeHue,
  oklabToOklch,
  oklchToHex,
  oklchToOklab,
  srgbToHex,
  srgbToHsv,
  srgbToLinear,
  srgbToOklab,
  oklabToSrgb,
} from "../docs/assets/colors.js";

const close = (actual, expected, tolerance = 1e-7) => {
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} should be close to ${expected}`);
};

test("hex and sRGB conversion handles short hex and round trips", () => {
  assert.deepEqual(hexToSrgb("#0f8"), { r: 0, g: 1, b: 136 / 255 });
  assert.equal(srgbToHex(hexToSrgb("336699")), "#336699");
  assert.throws(() => hexToSrgb("not-a-color"), /Invalid hex color/);
});

test("HSV converts known primary and secondary colors to sRGB", () => {
  assert.deepEqual(hsvToSrgb({ h: 0, s: 1, v: 1 }), { r: 1, g: 0, b: 0 });
  assert.deepEqual(hsvToSrgb({ h: 120, s: 1, v: 1 }), { r: 0, g: 1, b: 0 });
  assert.deepEqual(hsvToSrgb({ h: 240, s: 1, v: 1 }), { r: 0, g: 0, b: 1 });
  assert.deepEqual(hsvToSrgb({ h: 420, s: 1, v: 1 }), { r: 1, g: 1, b: 0 });
});

test("sRGB and HSV round trip", () => {
  const input = { r: 0.2, g: 0.7, b: 0.45 };
  const hsv = srgbToHsv(input);
  const output = hsvToSrgb(hsv);
  close(output.r, input.r);
  close(output.g, input.g);
  close(output.b, input.b);
  assert.deepEqual(srgbToHsv({ r: 0.4, g: 0.4, b: 0.4 }), { h: 0, s: 0, v: 0.4 });
});

test("sRGB transfer functions round trip representative channels", () => {
  const input = { r: 0, g: 0.18, b: 1 };
  const output = linearToSrgb(srgbToLinear(input));
  close(output.r, input.r);
  close(output.g, input.g);
  close(output.b, input.b);
});

test("sRGB and OKLab round trip", () => {
  const input = hexToSrgb("#d24a83");
  const output = oklabToSrgb(srgbToOklab(input));
  close(output.r, input.r, 2e-7);
  close(output.g, input.g, 2e-7);
  close(output.b, input.b, 2e-7);
});

test("OKLab and OKLCH round trip and normalize hue", () => {
  assert.equal(normalizeHue(-30), 330);
  assert.equal(normalizeHue(390), 30);
  const lab = { L: 0.62, a: -0.11, b: 0.08 };
  const output = oklchToOklab(oklabToOklch(lab));
  close(output.L, lab.L);
  close(output.a, lab.a);
  close(output.b, lab.b);
});

test("known white and black conversions remain neutral", () => {
  const white = hexToOklch("#ffffff");
  const black = hexToOklch("#000000");
  close(white.L, 1, 2e-7);
  close(white.C, 0, 2e-7);
  close(black.L, 0);
  close(black.C, 0);
});

test("in-gamut OKLCH is not chroma-mapped", () => {
  const input = hexToOklch("#4285f4");
  const result = mapOklchToSrgb(input);
  assert.equal(result.wasMapped, false);
  close(result.mapped.C, input.C);
  assert.equal(srgbToHex(result.srgb), "#4285f4");
});

test("out-of-gamut OKLCH is mapped by chroma only", () => {
  const input = { L: 0.7, C: 0.5, h: 40 };
  assert.equal(isOklchInSrgbGamut(input), false);
  const result = mapOklchToSrgb(input);
  assert.equal(result.wasMapped, true);
  assert.equal(result.mapped.L, input.L);
  assert.equal(result.mapped.h, input.h);
  assert.ok(result.mapped.C < input.C);
  assert.equal(isOklchInSrgbGamut(result.mapped), true);
  assert.match(oklchToHex(input), /^#[\da-f]{6}$/);
});
