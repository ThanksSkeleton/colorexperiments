#!/usr/bin/env python3
"""Generate an OKLCH polar-boundary lookup for GRACoL2013 CRPC6.

The script uses LittleCMS through ctypes. It converts each requested OKLCH
coordinate to ICC CIELAB D50, separates it through the registered
GRACoL2013_CRPC6 profile with relative-colorimetric intent, converts the CMYK
result back to Lab, and considers the coordinate printable when the CIEDE2000
round-trip error is no greater than the configured tolerance.

By default the registered profile is downloaded to a temporary file. Pass
--profile to work entirely from a local copy instead.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import hashlib
import json
import math
import tempfile
import urllib.request
from pathlib import Path


PROFILE_URL = (
    "https://registry.color.org/profile-registry/profiles/GRACoL2013_CRPC6.icc"
)
EXPECTED_PROFILE_ID = "978f11fd9202f7de7acf16acc355750a"
DEFAULT_OUTPUT = Path("docs/assets/gracol2013_crpc6_oklch_boundary.json")

# LittleCMS formatter constants from lcms2.h.
PT_CMYK = 6
PT_LAB = 10
TYPE_CMYK_DBL = (1 << 22) | (PT_CMYK << 16) | (4 << 3)
TYPE_LAB_DBL = (1 << 22) | (PT_LAB << 16) | (3 << 3)
INTENT_RELATIVE_COLORIMETRIC = 1

D50 = (0.9642956764295677, 1.0, 0.8251046025104602)
D65_TO_D50 = (
    (1.0479298208405488, 0.022946793341019088, -0.05019222954313557),
    (0.029627815688159344, 0.990434484573249, -0.01707382502938514),
    (-0.009243058152591178, 0.015055144896577895, 0.7518742899580008),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, help="Local GRACoL ICC profile")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--lightness-step", type=float, default=0.01)
    parser.add_argument("--hue-step", type=int, default=1)
    parser.add_argument("--max-chroma", type=float, default=0.5)
    parser.add_argument("--delta-e", type=float, default=1.0)
    parser.add_argument("--iterations", type=int, default=14)
    return parser.parse_args()


def multiply_matrix_vector(matrix, vector):
    return tuple(sum(row[i] * vector[i] for i in range(3)) for row in matrix)


def oklch_to_lab_d50(lightness: float, chroma: float, hue: float):
    angle = math.radians(hue)
    a = chroma * math.cos(angle)
    b = chroma * math.sin(angle)

    l_ = lightness + 0.3963377773761749 * a + 0.2158037573099136 * b
    m_ = lightness - 0.1055613458156586 * a - 0.0638541728258133 * b
    s_ = lightness - 0.0894841775298119 * a - 1.2914855480194092 * b
    l, m, s = l_**3, m_**3, s_**3
    xyz_d65 = (
        1.2268798758459243 * l - 0.5578149944602171 * m + 0.2813910456659647 * s,
        -0.0405757452148008 * l + 1.1122868032803170 * m - 0.0717110580655164 * s,
        -0.0763729366746601 * l - 0.4214933324022432 * m + 1.5869240198367816 * s,
    )
    xyz = multiply_matrix_vector(D65_TO_D50, xyz_d65)

    epsilon = 216 / 24389
    kappa = 24389 / 27

    def f(value):
        return math.cbrt(value) if value > epsilon else (kappa * value + 16) / 116

    fx, fy, fz = (f(xyz[i] / D50[i]) for i in range(3))
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e_2000(lab1, lab2):
    """CIEDE2000 with unit weighting factors."""
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2
    c1 = math.hypot(a1, b1)
    c2 = math.hypot(a2, b2)
    c_bar = (c1 + c2) / 2
    g = 0.5 * (1 - math.sqrt(c_bar**7 / (c_bar**7 + 25**7)))
    ap1, ap2 = (1 + g) * a1, (1 + g) * a2
    cp1, cp2 = math.hypot(ap1, b1), math.hypot(ap2, b2)

    def hue(ap, b):
        if ap == 0 and b == 0:
            return 0.0
        return math.degrees(math.atan2(b, ap)) % 360

    hp1, hp2 = hue(ap1, b1), hue(ap2, b2)
    dl = l2 - l1
    dc = cp2 - cp1
    dh_raw = hp2 - hp1
    if cp1 * cp2 == 0:
        dh = 0.0
    elif abs(dh_raw) <= 180:
        dh = dh_raw
    elif dh_raw > 180:
        dh = dh_raw - 360
    else:
        dh = dh_raw + 360
    dh_term = 2 * math.sqrt(cp1 * cp2) * math.sin(math.radians(dh / 2))

    l_bar = (l1 + l2) / 2
    cp_bar = (cp1 + cp2) / 2
    if cp1 * cp2 == 0:
        hp_bar = hp1 + hp2
    elif abs(hp1 - hp2) <= 180:
        hp_bar = (hp1 + hp2) / 2
    elif hp1 + hp2 < 360:
        hp_bar = (hp1 + hp2 + 360) / 2
    else:
        hp_bar = (hp1 + hp2 - 360) / 2

    t = (
        1
        - 0.17 * math.cos(math.radians(hp_bar - 30))
        + 0.24 * math.cos(math.radians(2 * hp_bar))
        + 0.32 * math.cos(math.radians(3 * hp_bar + 6))
        - 0.20 * math.cos(math.radians(4 * hp_bar - 63))
    )
    sl = 1 + 0.015 * (l_bar - 50) ** 2 / math.sqrt(20 + (l_bar - 50) ** 2)
    sc = 1 + 0.045 * cp_bar
    sh = 1 + 0.015 * cp_bar * t
    rt = -2 * math.sqrt(cp_bar**7 / (cp_bar**7 + 25**7)) * math.sin(
        math.radians(60 * math.exp(-((hp_bar - 275) / 25) ** 2))
    )
    x, y, z = dl / sl, dc / sc, dh_term / sh
    return math.sqrt(x * x + y * y + z * z + rt * y * z)


class LittleCms:
    def __init__(self, profile_path: Path):
        library_name = ctypes.util.find_library("lcms2")
        if not library_name:
            raise RuntimeError("LittleCMS 2 runtime (liblcms2) was not found")
        self.lib = ctypes.CDLL(library_name)
        self._declare_api()
        self.lab_profile = self.lib.cmsCreateLab4Profile(None)
        self.print_profile = self.lib.cmsOpenProfileFromFile(
            str(profile_path).encode(), b"r"
        )
        if not self.lab_profile or not self.print_profile:
            self.close()
            raise RuntimeError("LittleCMS could not open the ICC profiles")
        self.to_cmyk = self.lib.cmsCreateTransform(
            self.lab_profile,
            TYPE_LAB_DBL,
            self.print_profile,
            TYPE_CMYK_DBL,
            INTENT_RELATIVE_COLORIMETRIC,
            0,
        )
        self.to_lab = self.lib.cmsCreateTransform(
            self.print_profile,
            TYPE_CMYK_DBL,
            self.lab_profile,
            TYPE_LAB_DBL,
            INTENT_RELATIVE_COLORIMETRIC,
            0,
        )
        if not self.to_cmyk or not self.to_lab:
            self.close()
            raise RuntimeError("LittleCMS could not create the round-trip transforms")

    def _declare_api(self):
        handle = ctypes.c_void_p
        self.lib.cmsCreateLab4Profile.argtypes = [ctypes.c_void_p]
        self.lib.cmsCreateLab4Profile.restype = handle
        self.lib.cmsOpenProfileFromFile.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.cmsOpenProfileFromFile.restype = handle
        self.lib.cmsCreateTransform.argtypes = [
            handle,
            ctypes.c_uint32,
            handle,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]
        self.lib.cmsCreateTransform.restype = handle
        self.lib.cmsDoTransform.argtypes = [
            handle,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
        ]
        self.lib.cmsDeleteTransform.argtypes = [handle]
        self.lib.cmsCloseProfile.argtypes = [handle]

    def round_trip(self, labs):
        count = len(labs)
        lab_in = (ctypes.c_double * (count * 3))(
            *(component for lab in labs for component in lab)
        )
        cmyk = (ctypes.c_double * (count * 4))()
        lab_out = (ctypes.c_double * (count * 3))()
        self.lib.cmsDoTransform(self.to_cmyk, lab_in, cmyk, count)
        self.lib.cmsDoTransform(self.to_lab, cmyk, lab_out, count)
        return [tuple(lab_out[i * 3 : i * 3 + 3]) for i in range(count)]

    def close(self):
        for attribute in ("to_cmyk", "to_lab"):
            value = getattr(self, attribute, None)
            if value:
                self.lib.cmsDeleteTransform(value)
                setattr(self, attribute, None)
        for attribute in ("lab_profile", "print_profile"):
            value = getattr(self, attribute, None)
            if value:
                self.lib.cmsCloseProfile(value)
                setattr(self, attribute, None)


def profile_id(data: bytes) -> str:
    if len(data) < 128 or data[36:40] != b"acsp":
        raise ValueError("Downloaded file is not an ICC profile")
    return data[84:100].hex()


def acquire_profile(path: Path | None):
    if path:
        data = path.read_bytes()
        return path, data, None
    request = urllib.request.Request(PROFILE_URL, headers={"User-Agent": "colorexperiments/1"})
    with urllib.request.urlopen(request) as response:
        data = response.read()
    temporary = tempfile.NamedTemporaryFile(suffix=".icc", delete=False)
    temporary.write(data)
    temporary.close()
    return Path(temporary.name), data, Path(temporary.name)


def validate_arguments(args):
    if not 0 < args.lightness_step <= 1:
        raise ValueError("--lightness-step must be in (0, 1]")
    if args.hue_step <= 0 or 360 % args.hue_step:
        raise ValueError("--hue-step must be a positive divisor of 360")
    if args.max_chroma <= 0 or args.delta_e <= 0 or args.iterations <= 0:
        raise ValueError("chroma, Delta E, and iteration values must be positive")


def make_boundary(cms: LittleCms, args):
    hues = list(range(0, 360, args.hue_step))
    lightness_count = round(1 / args.lightness_step)
    lightnesses = [min(1.0, i * args.lightness_step) for i in range(lightness_count + 1)]
    rows = []
    truncated = 0

    for lightness in lightnesses:
        neutral = oklch_to_lab_d50(lightness, 0, 0)
        neutral_back = cms.round_trip([neutral])[0]
        neutral_error = delta_e_2000(neutral, neutral_back)
        if neutral_error > args.delta_e:
            rows.append({"l": round(lightness, 6), "c": [None] * len(hues)})
            continue

        low = [0.0] * len(hues)
        high = [args.max_chroma] * len(hues)
        high_labs = [oklch_to_lab_d50(lightness, args.max_chroma, hue) for hue in hues]
        high_back = cms.round_trip(high_labs)
        capped = [
            delta_e_2000(source, result) <= args.delta_e
            for source, result in zip(high_labs, high_back)
        ]
        truncated += sum(capped)

        for _ in range(args.iterations):
            active = [index for index, is_capped in enumerate(capped) if not is_capped]
            labs = [
                oklch_to_lab_d50(
                    lightness, (low[index] + high[index]) / 2, hues[index]
                )
                for index in active
            ]
            results = cms.round_trip(labs)
            for index, source, result in zip(active, labs, results):
                midpoint = (low[index] + high[index]) / 2
                if delta_e_2000(source, result) <= args.delta_e:
                    low[index] = midpoint
                else:
                    high[index] = midpoint

        boundary = [
            round(args.max_chroma if capped[index] else low[index], 6)
            for index in range(len(hues))
        ]
        rows.append({"l": round(lightness, 6), "c": boundary})

    return hues, rows, truncated


def main():
    args = parse_args()
    validate_arguments(args)
    profile_path, profile_data, temporary_path = acquire_profile(args.profile)
    try:
        actual_id = profile_id(profile_data)
        if actual_id != EXPECTED_PROFILE_ID:
            raise ValueError(
                f"Unexpected ICC profile ID {actual_id}; expected {EXPECTED_PROFILE_ID}"
            )
        cms = LittleCms(profile_path)
        try:
            hues, rows, truncated = make_boundary(cms, args)
        finally:
            cms.close()
    finally:
        if temporary_path:
            temporary_path.unlink(missing_ok=True)

    payload = {
        "schema": "colorexperiments.oklch-polar-gamut-boundary.v1",
        "profile": {
            "name": "GRACoL2013_CRPC6.icc",
            "registryUrl": PROFILE_URL,
            "iccProfileId": EXPECTED_PROFILE_ID,
            "sha256": hashlib.sha256(profile_data).hexdigest(),
        },
        "method": {
            "sourceSpace": "OKLCH (D65)",
            "connectionSpace": "CIELAB D50",
            "chromaticAdaptation": "Bradford D65 to D50",
            "cmm": "LittleCMS 2",
            "renderingIntent": "relative-colorimetric",
            "membership": "Lab to CMYK to Lab round trip",
            "deltaEFormula": "CIEDE2000",
            "deltaETolerance": args.delta_e,
            "binarySearchIterations": args.iterations,
        },
        "grid": {
            "lightnessStep": args.lightness_step,
            "hueStepDegrees": args.hue_step,
            "hues": hues,
            "maxChromaSearched": args.max_chroma,
            "truncatedBoundarySamples": truncated,
        },
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    print(f"Wrote {args.output} ({len(rows)} lightness rows × {len(hues)} hues)")
    if truncated:
        print(f"Warning: {truncated} boundaries reached --max-chroma")


if __name__ == "__main__":
    main()
