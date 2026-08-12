#!/usr/bin/env python3
"""Convert Munsell renotation ``all.dat`` data to CSV with OKLCH values.

The script has no third-party dependencies. By default it reads ``input/all.dat``
and writes ``input/all.csv`` relative to the repository root. Its default output
keeps only in-sRGB rows and adds one synthetic OKLCH midpoint between eligible
adjacent Munsell Value rows. Different paths can be supplied as positional args.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "input" / "all.dat"
DEFAULT_OUTPUT = REPO_ROOT / "input" / "all.csv"

# The RIT Munsell Renotation data states that x and y were calculated for CIE
# Illuminant C with the CIE 1931 2-degree observer. OKLab, and therefore OKLCH,
# is defined relative to D65. These normalized XYZ white points use Y = 1.
ILLUMINANT_C_XYZ = (0.98074, 1.0, 1.18232)
D65_XYZ = (0.95047, 1.0, 1.08883)

# Published renotation Y values use smoked magnesium oxide as their reference.
# RIT notes that multiplying them by 0.975 expresses them relative to a modern
# perfect reflecting diffuser. The original Y column is always preserved in the
# CSV; this factor is used only to derive OKLCH unless the CLI option disables it.
MAGNESIUM_OXIDE_Y_FACTOR = 0.975

# Bradford is a conventional chromatic-adaptation transform. Applying it makes
# the Illuminant-C XYZ values appropriate input to D65-based OKLab. Adaptation
# models perceived correspondence rather than a new spectral measurement.
BRADFORD = (
    (0.8951, 0.2664, -0.1614),
    (-0.7502, 1.7135, 0.0367),
    (0.0389, -0.0685, 1.0296),
)
BRADFORD_INVERSE = (
    (0.9869929, -0.1470543, 0.1599627),
    (0.4323053, 0.5183603, 0.0492912),
    (-0.0085287, 0.0400428, 0.9684867),
)


def matrix_vector(matrix: tuple[tuple[float, ...], ...], vector: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(sum(coefficient * value for coefficient, value in zip(row, vector)) for row in matrix)


def adapt_illuminant_c_to_d65(xyz: tuple[float, float, float]) -> tuple[float, float, float]:
    """Chromatically adapt XYZ from Illuminant C to D65 using Bradford CAT."""
    source_cone = matrix_vector(BRADFORD, ILLUMINANT_C_XYZ)
    target_cone = matrix_vector(BRADFORD, D65_XYZ)
    sample_cone = matrix_vector(BRADFORD, xyz)
    adapted_cone = tuple(
        sample * target / source
        for sample, source, target in zip(sample_cone, source_cone, target_cone)
    )
    return matrix_vector(BRADFORD_INVERSE, adapted_cone)  # type: ignore[return-value]


def xyy_to_xyz(x: float, y: float, luminance: float) -> tuple[float, float, float]:
    """Convert xyY to XYZ, where luminance is normalized to the 0..1 scale."""
    return (x * luminance / y, luminance, (1.0 - x - y) * luminance / y)


def signed_cube_root(value: float) -> float:
    # all.dat intentionally contains extrapolated, physically unreal colors.
    # A signed cube root keeps the numerical transform defined for their
    # potentially negative XYZ/LMS components; no gamut clipping is performed.
    return math.copysign(abs(value) ** (1.0 / 3.0), value)


def xyz_d65_to_oklch(xyz: tuple[float, float, float]) -> tuple[float, float, float | None]:
    """Convert D65-relative XYZ (Y=1 scale) to OKLCH; hue is in degrees."""
    x, y, z = xyz

    # XYZ-to-OKLab matrices from Bjorn Ottosson's definition of OKLab.
    l = 0.8190224379967030 * x + 0.3619062600528904 * y - 0.1288737815209879 * z
    m = 0.0329836539323885 * x + 0.9292868615863434 * y + 0.0361446663506424 * z
    s = 0.0481771893596242 * x + 0.2642395317527308 * y + 0.6335478284694309 * z
    l_root, m_root, s_root = map(signed_cube_root, (l, m, s))

    lightness = 0.2104542553 * l_root + 0.7936177850 * m_root - 0.0040720468 * s_root
    a = 1.9779984951 * l_root - 2.4285922050 * m_root + 0.4505937099 * s_root
    b = 0.0259040371 * l_root + 0.7827717662 * m_root - 0.8086757660 * s_root
    chroma = math.hypot(a, b)

    # Hue is mathematically undefined at zero chroma. A blank CSV cell conveys
    # that more honestly than assigning an arbitrary angle of zero degrees.
    hue = None if chroma < 1e-12 else math.degrees(math.atan2(b, a)) % 360.0
    return lightness, chroma, hue


def xyz_d65_to_srgb(
    xyz: tuple[float, float, float],
) -> tuple[tuple[float, float, float], bool]:
    """Convert D65 XYZ to unclamped, encoded sRGB and report gamut membership."""
    x, y, z = xyz
    linear = (
        3.2409699419 * x - 1.5373831776 * y - 0.4986107603 * z,
        -0.9692436363 * x + 1.8759675015 * y + 0.0415550574 * z,
        0.0556300797 * x - 0.2039769589 * y + 1.0569715142 * z,
    )

    # Test the linear channels before transfer encoding or clipping. A tiny
    # tolerance prevents matrix round-off from rejecting a boundary color.
    in_gamut = all(-1e-7 <= channel <= 1.0 + 1e-7 for channel in linear)

    def encode(channel: float) -> float:
        # Applying the sRGB transfer function without clamping deliberately
        # leaves out-of-gamut channels below 0 or above 1. That is more useful
        # analytical data than RGB values silently clipped to the display cube.
        if channel <= 0.0031308:
            return 12.92 * channel
        return 1.055 * channel ** (1.0 / 2.4) - 0.055

    return tuple(encode(channel) for channel in linear), in_gamut  # type: ignore[return-value]


def oklch_to_srgb(
    lightness: float, chroma: float, hue: float
) -> tuple[tuple[float, float, float], bool]:
    """Convert OKLCH to unclamped encoded sRGB and report gamut membership."""
    angle = math.radians(hue)
    a = chroma * math.cos(angle)
    b = chroma * math.sin(angle)
    l_root = lightness + 0.3963377774 * a + 0.2158037573 * b
    m_root = lightness - 0.1055613458 * a - 0.0638541728 * b
    s_root = lightness - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_root**3, m_root**3, s_root**3
    linear = (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )
    in_gamut = all(-1e-7 <= channel <= 1.0 + 1e-7 for channel in linear)

    def encode(channel: float) -> float:
        return (
            12.92 * channel
            if channel <= 0.0031308
            else 1.055 * channel ** (1.0 / 2.4) - 0.055
        )

    return tuple(encode(channel) for channel in linear), in_gamut  # type: ignore[return-value]


def interpolate_hue(first: float, second: float) -> float:
    """Return the midpoint along the shorter path between two hue angles."""
    difference = (second - first + 180.0) % 360.0 - 180.0
    return (first + difference / 2.0) % 360.0


def munsell_value_to_luminance(value: float) -> float:
    """Return neutral-axis luminance Y percent for a Munsell Value."""
    # ASTM D1535's fifth-order form of the Munsell value function.
    return (
        1.2219 * value
        - 0.23111 * value**2
        + 0.23951 * value**3
        - 0.021009 * value**4
        + 0.0008404 * value**5
    )


def make_neutral_row(value: float, fake: bool, correct_published_y: bool) -> dict[str, object]:
    """Create one displayable neutral-axis row in the published CSV schema."""
    published_y = munsell_value_to_luminance(value)
    luminance = published_y / 100.0
    if correct_published_y:
        luminance *= MAGNESIUM_OXIDE_Y_FACTOR

    # A neutral under Illuminant C has the white point's chromaticity. Adapt it
    # through the same C-to-D65 path as the chromatic renotation samples.
    x = ILLUMINANT_C_XYZ[0] / sum(ILLUMINANT_C_XYZ)
    y = ILLUMINANT_C_XYZ[1] / sum(ILLUMINANT_C_XYZ)
    xyz_d65 = adapt_illuminant_c_to_d65(xyy_to_xyz(x, y, luminance))
    oklch_l, _, _ = xyz_d65_to_oklch(xyz_d65)
    srgb, in_srgb_gamut = xyz_d65_to_srgb(xyz_d65)
    value_text = f"{value:.10g}"
    suffix = "x" if fake else ""
    return {
        "H": "N",
        "V": value_text,
        "C": "0",
        "MUNSELL_NAME": f"N {value_text}{suffix}",
        "x": "",
        "y": "",
        "Y": f"{published_y:.10g}",
        "OKLCH_L": oklch_l,
        "OKLCH_C": 0.0,
        "OKLCH_h": None,
        "sRGB": srgb,
        "IN_SRGB_GAMUT": in_srgb_gamut,
        "FAKE_MUNSEL": fake,
    }


def convert(
    input_path: Path,
    output_path: Path,
    correct_published_y: bool,
    in_srgb_only: bool = True,
    interpolate_fake_munsell: bool = True,
) -> int:
    rows: list[dict[str, object]] = []
    original_values: set[float] = set()
    with input_path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            fields = line.split()
            if not fields or fields[0] == "H":
                continue
            if len(fields) != 6:
                raise ValueError(f"{input_path}:{line_number}: expected 6 columns, found {len(fields)}")

            hue_name, value_text, chroma_text, x_text, y_text, luminance_text = fields
            original_values.add(float(value_text))
            x, y, published_y = map(float, (x_text, y_text, luminance_text))

            # all.dat records Y as a percentage. OKLab expects XYZ normalized so
            # the reference white has Y=1, hence division by 100 here.
            luminance = published_y / 100.0
            if correct_published_y:
                luminance *= MAGNESIUM_OXIDE_Y_FACTOR

            # One extrapolated "unreal" row in all.dat has y=0. xyY cannot be
            # converted to XYZ in that case because the defining equations
            # divide by y. Its derived fields remain undefined.
            if y == 0:
                oklch_l = oklch_c = oklch_h = None
                srgb = (None, None, None)
                in_srgb_gamut = None
            else:
                xyz_c = xyy_to_xyz(x, y, luminance)
                xyz_d65 = adapt_illuminant_c_to_d65(xyz_c)
                oklch_l, oklch_c, oklch_h = xyz_d65_to_oklch(xyz_d65)
                srgb, in_srgb_gamut = xyz_d65_to_srgb(xyz_d65)

            rows.append(
                {
                    "H": hue_name,
                    "V": value_text,
                    "C": chroma_text,
                    "MUNSELL_NAME": f"{hue_name} {value_text}/{chroma_text}",
                    "x": x_text,
                    "y": y_text,
                    "Y": luminance_text,
                    "OKLCH_L": oklch_l,
                    "OKLCH_C": oklch_c,
                    "OKLCH_h": oklch_h,
                    "sRGB": srgb,
                    "IN_SRGB_GAMUT": in_srgb_gamut,
                    "FAKE_MUNSEL": False,
                }
            )

    if interpolate_fake_munsell:
        groups: dict[tuple[str, str], list[dict[str, object]]] = {}
        for row in rows:
            groups.setdefault((str(row["H"]), str(row["C"])), []).append(row)

        fake_rows: list[dict[str, object]] = []
        for group in groups.values():
            group.sort(key=lambda row: float(str(row["V"])))
            for first, second in zip(group, group[1:]):
                # Synthetic points are made only from adjacent original rows.
                # Requiring one displayable endpoint avoids filling remote parts
                # of the extrapolated Munsell solid that have no relevance here.
                if not (first["IN_SRGB_GAMUT"] or second["IN_SRGB_GAMUT"]):
                    continue
                required = ("OKLCH_L", "OKLCH_C", "OKLCH_h")
                if any(first[key] is None or second[key] is None for key in required):
                    continue

                value = (float(str(first["V"])) + float(str(second["V"]))) / 2.0
                lightness = (float(first["OKLCH_L"]) + float(second["OKLCH_L"])) / 2.0
                chroma = (float(first["OKLCH_C"]) + float(second["OKLCH_C"])) / 2.0
                hue = interpolate_hue(float(first["OKLCH_h"]), float(second["OKLCH_h"]))
                srgb, in_gamut = oklch_to_srgb(lightness, chroma, hue)
                value_text = f"{value:.10g}"
                hue_name = str(first["H"])
                chroma_text = str(first["C"])
                fake_rows.append(
                    {
                        "H": hue_name,
                        "V": value_text,
                        "C": chroma_text,
                        "MUNSELL_NAME": f"{hue_name} {value_text}/{chroma_text}x",
                        "x": "",
                        "y": "",
                        "Y": "",
                        "OKLCH_L": lightness,
                        "OKLCH_C": chroma,
                        "OKLCH_h": hue,
                        "sRGB": srgb,
                        "IN_SRGB_GAMUT": in_gamut,
                        "FAKE_MUNSEL": True,
                    }
                )
        rows.extend(fake_rows)

    if in_srgb_only:
        rows = [row for row in rows if row["IN_SRGB_GAMUT"] is True]

    # Generate an achromatic counterpart for every Value that the chromatic
    # book can display. Values originating in all.dat are real neutral
    # notations; Values introduced by midpoint generation retain its synthetic
    # convention regardless of which hue/chroma first made them displayable.
    display_values = sorted({float(str(row["V"])) for row in rows})
    rows.extend(
        make_neutral_row(value, value not in original_values, correct_published_y)
        for value in display_values
    )

    with output_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow(
            (
                "H",
                "V",
                "C",
                "MUNSELL_NAME",
                "x",
                "y",
                "Y",
                "OKLCH_L",
                "OKLCH_C",
                "OKLCH_h",
                "sRGB_R",
                "sRGB_G",
                "sRGB_B",
                "IN_SRGB_GAMUT",
                "FAKE_MUNSEL",
            )
        )
        for row in rows:
            srgb = row["sRGB"]
            writer.writerow(
                (
                    row["H"], row["V"], row["C"], row["MUNSELL_NAME"],
                    row["x"], row["y"], row["Y"],
                    *("" if row[key] is None else f"{float(row[key]):.10g}"
                      for key in ("OKLCH_L", "OKLCH_C", "OKLCH_h")),
                    *("" if channel is None else f"{channel:.10g}" for channel in srgb),
                    "" if row["IN_SRGB_GAMUT"] is None else str(row["IN_SRGB_GAMUT"]).upper(),
                    str(row["FAKE_MUNSEL"]).upper(),
                )
            )
    return len(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--preserve-published-y-scale",
        action="store_true",
        help="Do not apply RIT's suggested 0.975 correction when deriving OKLCH.",
    )
    parser.add_argument(
        "--include-out-of-srgb",
        action="store_true",
        help="Include rows outside sRGB; by default only in-gamut rows are written.",
    )
    parser.add_argument(
        "--no-interpolate-fake-munsell",
        action="store_true",
        help="Do not generate synthetic OKLCH midpoints between adjacent Value rows.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = convert(
        args.input,
        args.output,
        not args.preserve_published_y_scale,
        in_srgb_only=not args.include_out_of_srgb,
        interpolate_fake_munsell=not args.no_interpolate_fake_munsell,
    )
    print(f"Wrote {count} rows to {args.output}")


if __name__ == "__main__":
    main()
