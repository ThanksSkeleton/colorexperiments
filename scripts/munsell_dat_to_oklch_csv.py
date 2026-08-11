#!/usr/bin/env python3
"""Convert Munsell renotation ``all.dat`` data to CSV with OKLCH values.

The script has no third-party dependencies. By default it reads ``input/all.dat``
and writes ``input/all.csv`` relative to the repository root. Different paths can
be supplied as the first and second positional arguments.
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


def convert(input_path: Path, output_path: Path, correct_published_y: bool) -> int:
    row_count = 0
    with input_path.open(encoding="utf-8") as source, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as destination:
        writer = csv.writer(destination)
        writer.writerow(
            (
                "H",
                "V",
                "C",
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
            )
        )

        for line_number, line in enumerate(source, start=1):
            fields = line.split()
            if not fields or fields[0] == "H":
                continue
            if len(fields) != 6:
                raise ValueError(f"{input_path}:{line_number}: expected 6 columns, found {len(fields)}")

            hue_name, value_text, chroma_text, x_text, y_text, luminance_text = fields
            x, y, published_y = map(float, (x_text, y_text, luminance_text))

            # all.dat records Y as a percentage. OKLab expects XYZ normalized so
            # the reference white has Y=1, hence division by 100 here.
            luminance = published_y / 100.0
            if correct_published_y:
                luminance *= MAGNESIUM_OXIDE_Y_FACTOR

            # One extrapolated "unreal" row in all.dat has y=0. xyY cannot be
            # converted to XYZ in that case because the defining equations
            # divide by y. Preserve the source row and leave all derived fields
            # blank rather than dropping it or fabricating finite coordinates.
            if y == 0:
                oklch_l = oklch_c = oklch_h = None
                srgb = (None, None, None)
                in_srgb_gamut = None
            else:
                xyz_c = xyy_to_xyz(x, y, luminance)
                xyz_d65 = adapt_illuminant_c_to_d65(xyz_c)
                oklch_l, oklch_c, oklch_h = xyz_d65_to_oklch(xyz_d65)
                srgb, in_srgb_gamut = xyz_d65_to_srgb(xyz_d65)

            # Original strings are emitted unchanged so the source columns do
            # not acquire formatting noise. Derived values get useful precision.
            writer.writerow(
                (
                    hue_name,
                    value_text,
                    chroma_text,
                    x_text,
                    y_text,
                    luminance_text,
                    "" if oklch_l is None else f"{oklch_l:.10g}",
                    "" if oklch_c is None else f"{oklch_c:.10g}",
                    "" if oklch_h is None else f"{oklch_h:.10g}",
                    *("" if channel is None else f"{channel:.10g}" for channel in srgb),
                    "" if in_srgb_gamut is None else str(in_srgb_gamut).upper(),
                )
            )
            row_count += 1

    return row_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--preserve-published-y-scale",
        action="store_true",
        help="Do not apply RIT's suggested 0.975 correction when deriving OKLCH.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = convert(args.input, args.output, not args.preserve_published_y_scale)
    print(f"Wrote {count} rows to {args.output}")


if __name__ == "__main__":
    main()
