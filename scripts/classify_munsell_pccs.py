#!/usr/bin/env python3
"""Classify a Munsell CSV into PCCS tone categories.

This is a small, dependency-free extraction of the useful mathematics from
Masaaki Shibata's MIT-licensed ``pccs`` 0.2a3 package.  It is intended for
offline preprocessing; the generated classifications can then be consumed by
the project's static browser experiments without shipping Python, NumPy,
SymPy, or colour-science.

Portions derived from pccs 0.2a3:

    Copyright (c) 2021 Masaaki Shibata

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to permit
    persons to whom the Software is furnished to do so, subject to the
    following conditions:

    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
    NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
    USE OR OTHER DEALINGS IN THE SOFTWARE.

The Munsell-to-PCCS conversion follows the package's implementation of:

    Kobayashi, Mituo; and Yosiki, Kayoko. 2001. Mathematical Relation
    among PCCS Tones, PCCS Color Attributes and Munsell Color Attributes.
    Journal of the Color Science Association of Japan 25 (4), 249-261.

The source package rounded PCCS hue, lightness, and saturation to the nearest
0.5 before choosing a tone.  This script can reproduce that old behavior or
use the continuous coordinates as the new behavior.  Combined with the two
distance formulas, this produces a 2x2 comparison of category answers.

The additional Paper 2001 category follows the independently supplied
``INPUT/munsell_to_pccs.py`` transcription. Its important difference from
pccs 0.2a3 is the paper's hue-dependent chroma term:

    12 + 1.7 * sin((h + 2.2) * pi / 12)

The rejected package instead calculated ``sin(h + 2.2*pi/12)``. The Paper
2001 category uses continuous coordinates and corrected Euclidean distance.

Example:

    python3 scripts/classify_munsell_pccs.py \
        docs/assets/munsell_renotation_oklch.csv \
        --output INPUT/munsell_pccs.csv \
        --distance-formula both \
        --rounding both
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TextIO


PCCS_TONE_COORDS: dict[str, tuple[float, float]] = {
    # tone: (representative saturation, representative tone-lightness)
    "p": (2.0, 8.6),
    "p+": (3.0, 8.2),
    "ltg": (2.0, 7.1),
    "g": (2.0, 4.1),
    "dkg": (2.0, 2.1),
    "lt": (5.0, 7.8),
    "lt+": (6.0, 7.3),
    "sf": (5.0, 6.3),
    "d": (5.0, 4.8),
    "dk": (5.0, 3.0),
    "b": (8.0, 6.6),
    "s": (8.0, 5.2),
    "dp": (8.0, 4.1),
    "v": (9.0, 5.5),
}

# These numeric codes reproduce colour-science's Munsell specification:
# B=1, BG=2, G=3, GY=4, Y=5, YR=6, R=7, RP=8, P=9, PB=10.
MUNSELL_HUE_CODES: dict[str, float] = {
    "B": 1.0,
    "BG": 2.0,
    "G": 3.0,
    "GY": 4.0,
    "Y": 5.0,
    "YR": 6.0,
    "R": 7.0,
    "RP": 8.0,
    "P": 9.0,
    "PB": 10.0,
}


def round_to_half(value: float) -> float:
    """Reproduce NumPy's half-to-even rounding on a 0.5-unit grid.

    Python's round(), like NumPy's round() under ordinary finite inputs, uses
    ties-to-even.  Multiplication by 2 turns half units into integers before
    rounding.  For example, 4.25 becomes 4.0 while 4.75 becomes 5.0.
    """

    return round(value * 2.0) / 2.0


def parse_munsell_hue(hue: str) -> tuple[float, float] | None:
    """Return a Munsell (hue step, hue-code number), or None for neutral."""

    hue = hue.strip().upper()
    if hue == "N":
        return None

    for letters in sorted(MUNSELL_HUE_CODES, key=len, reverse=True):
        if hue.endswith(letters):
            step_text = hue[: -len(letters)]
            if not step_text:
                break
            return float(step_text), MUNSELL_HUE_CODES[letters]

    raise ValueError(f"invalid Munsell hue: {hue!r}")


def munsell_hue_to_linear_scale(step: float, code: float) -> float:
    """Convert a Munsell hue specification to the package's 0-100 scale."""

    high = (10.0 - (code - 1.0) + 6.0) % 10.0
    return (high * 10.0 + step) % 100.0


def pccs_chroma_limit(hue: float) -> float:
    """Return the hue-dependent chroma term used by pccs 0.2a3.

    The parentheses below deliberately preserve the published package code,
    including its potentially surprising placement.  It should be verified
    against the cited paper before being treated as an independent correction.
    """

    return 12.0 + 1.7 * math.sin(hue + (2.2 / 12.0 * math.pi))


def paper_2001_chroma_limit(hue: float) -> float:
    """Return the hue-dependent chroma term transcribed from the 2001 paper.

    Unlike pccs_chroma_limit(), the entire ``h + 2.2`` hue expression is
    converted to radians by multiplying it by pi/12.
    """

    return 12.0 + 1.7 * math.sin((hue + 2.2) * math.pi / 12.0)


def pccs_lightness_coefficient(hue: float) -> float:
    """Return the package's hue-dependent lightness coefficient."""

    return 0.81 - 0.24 * math.sin((hue - 2.6) / 12.0 * math.pi)


def munsell_to_pccs(
    hue_name: str,
    value: float,
    chroma: float,
    chroma_limit: Callable[[float], float] = pccs_chroma_limit,
) -> tuple[float, float, float]:
    """Convert Munsell H, V, C to continuous PCCS h, l, s coordinates.

    The original used SymPy to solve the saturation quadratic.  Only its
    positive root is relevant, so the quadratic formula is used directly.
    """

    parsed_hue = parse_munsell_hue(hue_name)
    if parsed_hue is None or chroma == 0.0:
        return 0.0, value, 0.0

    step, code = parsed_hue
    linear_hue = munsell_hue_to_linear_scale(step, code)
    y = linear_hue / 50.0 * math.pi
    hue = (
        (24.0 / (2.0 * math.pi)) * y
        + 1.24
        + 0.020 * math.cos(y)
        - 0.10 * math.cos(2.0 * y)
        - 0.11 * math.cos(3.0 * y)
        + 0.68 * math.sin(y)
        - 0.30 * math.sin(2.0 * y)
        + 0.013 * math.sin(3.0 * y)
    )

    denominator = chroma_limit(hue) * (
        1.0 - math.exp(-pccs_lightness_coefficient(hue) * value)
    )
    if denominator == 0.0:
        raise ValueError("PCCS saturation is undefined at this Munsell value")

    # Solve 0.004*s^2 + 0.077*s - chroma/denominator = 0 and retain
    # the positive root, matching max(sympy.solve(...)) in pccs 0.2a3.
    a = 0.0040
    b = 0.077
    q = chroma / denominator
    saturation = (-b + math.sqrt(b * b + 4.0 * a * q)) / (2.0 * a)
    return hue, value, saturation


def tone_lightness(hue: float, lightness: float, saturation: float) -> float:
    """Transform PCCS lightness into the tone diagram's t coordinate."""

    adjustment = 0.25 - 0.34 * math.sqrt(
        1.0 - math.sin((hue - 2.0) / 12.0 * math.pi)
    )
    return lightness - adjustment * saturation


def old_tone_distance(
    saturation: float,
    tone_value: float,
    reference_saturation: float,
    reference_tone_value: float,
) -> float:
    """Return the strange distance formula used by pccs 0.2a3.

    Legacy formula:

        ((reference_saturation - saturation)^2
         + (reference_tone_value - tone_value))^2

    The tone-lightness difference is *not* squared before being added, and
    then the entire possibly signed sum is squared.  Consequently a negative
    tone-lightness difference can cancel a positive squared saturation
    difference.  It is retained verbatim so old-package classifications can
    be reproduced and compared.
    """

    return (
        (reference_saturation - saturation) ** 2
        + (reference_tone_value - tone_value)
    ) ** 2


def corrected_tone_distance(
    saturation: float,
    tone_value: float,
    reference_saturation: float,
    reference_tone_value: float,
) -> float:
    """Return ordinary squared Euclidean distance in PCCS tone space.

    Corrected formula:

        (reference_saturation - saturation)^2
        + (reference_tone_value - tone_value)^2

    Both axes contribute non-negative squared differences.  Taking a square
    root is unnecessary because it would not change which tone is nearest.
    This correction assumes the two PCCS axes should have equal weight.
    """

    return (reference_saturation - saturation) ** 2 + (
        reference_tone_value - tone_value
    ) ** 2


DISTANCE_FORMULAS: dict[str, Callable[[float, float, float, float], float]] = {
    "old": old_tone_distance,
    "new": corrected_tone_distance,
}


def classify_tone(
    hue: float,
    lightness: float,
    saturation: float,
    distance_formula: str,
    excluded_tones: frozenset[str] = frozenset(),
) -> tuple[str, float]:
    """Return the nearest PCCS tone and its distance.

    The caller decides whether these coordinates are the legacy half-step
    values or the new continuous values.  Neutral colors are categorized
    separately by category_for().  Ties retain PCCS_TONE_COORDS insertion
    order, matching the old package.
    """

    tone_value = tone_lightness(hue, lightness, saturation)
    distance = DISTANCE_FORMULAS[distance_formula]
    tone = min(
        (name for name in PCCS_TONE_COORDS if name not in excluded_tones),
        key=lambda name: distance(
            saturation, tone_value, *PCCS_TONE_COORDS[name]
        ),
    )
    return tone, tone_value


def neutral_category(value: float) -> str:
    """Reproduce the package's short neutral labels."""

    if value >= 9.5:
        return "W"
    if value <= 1.5:
        return "Bk"
    return "Gy"


def category_for(
    hue: float,
    lightness: float,
    saturation: float,
    distance_formula: str,
    rounding: str,
    excluded_tones: frozenset[str] = frozenset(),
) -> str:
    """Classify one PCCS coordinate using the requested 2x2 variant."""

    if rounding == "old":
        hue = round_to_half(hue)
        lightness = round_to_half(lightness)
        saturation = round_to_half(saturation)
    elif rounding != "new":
        raise ValueError(f"unknown rounding mode: {rounding!r}")

    if hue == 0.0 and saturation == 0.0:
        return neutral_category(lightness)

    tone, _ = classify_tone(
        hue, lightness, saturation, distance_formula, excluded_tones
    )
    return tone


def tone_center_munsell(
    tone: str, hue: float
) -> tuple[float, float]:
    """Approximate a PCCS tone center as Munsell (Value, Chroma)."""

    saturation, tone_value = PCCS_TONE_COORDS[tone]
    value = tone_value + (
        0.25
        - 0.34 * math.sqrt(1.0 - math.sin((hue - 2.0) / 12.0 * math.pi))
    ) * saturation
    chroma = (
        0.004 * saturation**2 + 0.077 * saturation
    ) * paper_2001_chroma_limit(hue) * (
        1.0 - math.exp(-pccs_lightness_coefficient(hue) * value)
    )
    return value, chroma


def modified_pccs_exclusions(
    hue: float, value: float, chroma: float
) -> frozenset[str]:
    """Return tones forbidden by the project's modified-PCCS region rules."""

    centers = {
        tone: tone_center_munsell(tone, hue) for tone in ("dkg", "dk", "dp")
    }
    allowed = set(PCCS_TONE_COORDS)
    dp_value, dp_chroma = centers["dp"]
    dk_value, dk_chroma = centers["dk"]
    dkg_value, dkg_chroma = centers["dkg"]

    if value < dp_value and chroma > dp_chroma:
        allowed = {"dp"}
    if value < dp_value and chroma < dp_chroma:
        allowed = {"dp", "d", "g", "dk", "dkg"}
    if value < dk_value and chroma < dk_chroma:
        allowed = {"dk", "g", "dkg"}
    if value < dkg_value and chroma < dkg_chroma:
        allowed = {"dkg"}

    return frozenset(PCCS_TONE_COORDS.keys() - allowed)


def classify_row(
    row: dict[str, str],
    distance_formulas: Iterable[str],
    rounding_modes: Iterable[str],
    include_modified_pccs: bool,
) -> dict[str, str]:
    """Append only the selected PCCS category answers to one CSV row."""

    hue, lightness, saturation = munsell_to_pccs(
        row["H"], float(row["V"]), float(row["C"])
    )

    categories = {
        category_field(distance_formula, rounding): category_for(
            hue,
            lightness,
            saturation,
            distance_formula,
            rounding,
        )
        for distance_formula in distance_formulas
        for rounding in rounding_modes
    }
    paper_hue, paper_lightness, paper_saturation = munsell_to_pccs(
        row["H"],
        float(row["V"]),
        float(row["C"]),
        chroma_limit=paper_2001_chroma_limit,
    )
    categories[PAPER_2001_CATEGORY_FIELD] = category_for(
        paper_hue, paper_lightness, paper_saturation, "new", "new"
    )
    if include_modified_pccs:
        categories[MODIFIED_PCCS_CATEGORY_FIELD] = category_for(
            paper_hue,
            paper_lightness,
            paper_saturation,
            "new",
            "new",
            modified_pccs_exclusions(
                paper_hue, float(row["V"]), float(row["C"])
            ),
        )
    return {**row, **categories}


def category_field(distance_formula: str, rounding: str) -> str:
    """Return the CSV heading for one category-answer variant."""

    return f"PCCS_CATEGORY_{distance_formula.upper()}_DISTANCE_{rounding.upper()}_ROUNDING"


PAPER_2001_CATEGORY_FIELD = "PCCS_CATEGORY_PAPER_2001"
MODIFIED_PCCS_CATEGORY_FIELD = "PCCS_CATEGORY_MODIFIED_PCCS"
MIN_MUNSELL_VALUE = 1.0


def classify_csv(
    source: TextIO,
    destination: TextIO,
    distance_formulas: Iterable[str],
    rounding_modes: Iterable[str],
    include_modified_pccs: bool = False,
) -> None:
    """Read a Munsell CSV and write it with appended PCCS fields."""

    reader = csv.DictReader(source)
    required_fields = {"H", "V", "C"}
    if reader.fieldnames is None or not required_fields.issubset(reader.fieldnames):
        missing = required_fields.difference(reader.fieldnames or ())
        raise ValueError(f"input CSV is missing required columns: {sorted(missing)}")

    distance_formulas = tuple(distance_formulas)
    rounding_modes = tuple(rounding_modes)
    category_fields = [
        category_field(distance_formula, rounding)
        for distance_formula in distance_formulas
        for rounding in rounding_modes
    ]
    paper_fields = [PAPER_2001_CATEGORY_FIELD]
    if include_modified_pccs:
        paper_fields.append(MODIFIED_PCCS_CATEGORY_FIELD)
    writer = csv.DictWriter(
        destination,
        fieldnames=[*reader.fieldnames, *category_fields, *paper_fields],
        lineterminator="\n",
    )
    writer.writeheader()
    for row in reader:
        if float(row["V"]) < MIN_MUNSELL_VALUE:
            continue
        writer.writerow(classify_row(
            row, distance_formulas, rounding_modes, include_modified_pccs
        ))


def parse_args(arguments: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CSV containing H, V, and C columns")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output CSV path; defaults to standard output",
    )
    parser.add_argument(
        "--distance-formula",
        choices=[*DISTANCE_FORMULAS, "both"],
        default="both",
        help="tone distance calculation(s) to use (default: both)",
    )
    parser.add_argument(
        "--rounding",
        choices=["old", "new", "both"],
        default="both",
        help="old half-step or new continuous coordinates (default: both)",
    )
    parser.add_argument(
        "--modified-pccs",
        action="store_true",
        help="append the modified-PCCS category using special Vivid/Deep rules",
    )
    return parser.parse_args(arguments)


def main(arguments: Iterable[str] | None = None) -> int:
    args = parse_args(arguments)
    distance_formulas = (
        tuple(DISTANCE_FORMULAS)
        if args.distance_formula == "both"
        else (args.distance_formula,)
    )
    rounding_modes = (
        ("old", "new") if args.rounding == "both" else (args.rounding,)
    )

    with args.input.open("r", encoding="utf-8", newline="") as source:
        if args.output is None:
            classify_csv(
                source, sys.stdout, distance_formulas, rounding_modes,
                args.modified_pccs,
            )
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("w", encoding="utf-8", newline="") as destination:
                classify_csv(
                    source, destination, distance_formulas, rounding_modes,
                    args.modified_pccs,
                )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
