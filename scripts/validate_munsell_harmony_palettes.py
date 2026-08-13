#!/usr/bin/env python3
"""Generate validation data for MUNSEL HARMONY BOOK tonal palettes.

The script emits one CSV row for every contextual combination of input hue,
harmony, harmony member, and tonal relationship. Symmetric/equivalent hue-pair
calculations are cached, while the complete contextual result set is retained.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "docs/assets/munsell_renotation_oklch.csv"
DEFAULT_OUTPUT = ROOT / "munsell_harmony_palette_validation.csv"

HUE_FAMILIES = ("R", "YR", "Y", "GY", "G", "BG", "B", "PB", "P", "RP")
HUE_STEPS = (2.5, 5, 7.5, 10)
HUES = tuple(f"{step:g}{family}" for family in HUE_FAMILIES for step in HUE_STEPS)

HARMONIES = (
    ("Analogous", ((3, "+3"), (-3, "-3"))),
    ("Complement", ((20, "+20"),)),
    ("Split complement", ((17, "+17"), (23, "+23"))),
    ("Triad", ((13, "+13"), (27, "+27"))),
    ("Square", ((10, "+10"), (20, "+20"), (30, "+30"))),
)
TONAL_RELATIONSHIPS = ("equal", "hierarchical")
VALUE_STEP = 0.5
CHROMA_STEP = 2
EXTENDED_CHROMA_STEPS = -2
VALUE_STEP_OFFSETS = (0, 3, 6, 9, -3, -6, -9)
MIN_MUNSELL_VALUE = 1.0


@dataclass(frozen=True)
class Color:
    hue: str
    value: float
    chroma: int
    name: str


@dataclass(frozen=True)
class Extension:
    colors: tuple[Color, ...]
    malformed: bool
    sidedness: str


def number_key(number: float) -> float:
    """Normalize coordinates used as dictionary keys."""
    return round(number, 10)


def load_colors(path: Path) -> tuple[dict[tuple[str, float, int], Color], dict[str, tuple[Color, ...]]]:
    lookup: dict[tuple[str, float, int], Color] = {}
    by_hue_lists: dict[str, list[Color]] = {hue: [] for hue in HUES}
    with path.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            hue = row["H"]
            if hue == "N" or hue not in by_hue_lists or float(row["V"]) < MIN_MUNSELL_VALUE:
                continue
            color = Color(hue, number_key(float(row["V"])), int(float(row["C"])), row["MUNSELL_NAME"])
            lookup[(color.hue, color.value, color.chroma)] = color
            by_hue_lists[hue].append(color)
    missing = [hue for hue, colors in by_hue_lists.items() if not colors]
    if missing:
        raise ValueError(f"Input is missing chromatic hue pages: {', '.join(missing)}")
    return lookup, {hue: tuple(colors) for hue, colors in by_hue_lists.items()}


def malformed_off_black(by_hue: dict[str, tuple[Color, ...]], hue: str, chroma: int) -> tuple[bool, str]:
    candidates = [color for color in by_hue[hue] if color.chroma == chroma]
    if not candidates:
        return True, "undefined"
    off_black = min(candidates, key=lambda color: color.value)
    malformed = off_black.value < MIN_MUNSELL_VALUE
    return malformed, off_black.name


def classify_sidedness(colors: tuple[Color, ...], anchor_value: float) -> str:
    has_equal = any(color.value == anchor_value for color in colors)
    has_lighter = any(color.value > anchor_value for color in colors)
    has_darker = any(color.value < anchor_value for color in colors)
    if has_lighter and has_darker:
        return "two-sided"
    if has_lighter and not has_darker:
        return "lighter-only"
    if has_darker and not has_lighter:
        return "darker-only"
    if has_equal:
        return "equal-only"
    return "neither"


def combine_sidedness(first: str, second: str) -> str:
    active = [side for side in (first, second) if side != "neither"]
    if not active:
        return "neither"
    if all(side == "two-sided" for side in active):
        return "two-sided"
    if all(side in ("lighter-only", "equal-only") for side in active) and any(side == "lighter-only" for side in active):
        return "lighter-only"
    if all(side in ("darker-only", "equal-only") for side in active) and any(side == "darker-only" for side in active):
        return "darker-only"
    if all(side == "equal-only" for side in active):
        return "equal-only"
    return "mixed"


def build_validator(lookup: dict[tuple[str, float, int], Color], by_hue: dict[str, tuple[Color, ...]]):
    @lru_cache(maxsize=None)
    def superior_brightest(hue: str) -> Color:
        return max(by_hue[hue], key=lambda color: (color.chroma, color.value))

    @lru_cache(maxsize=None)
    def canonical_equal_brightests(first_hue: str, second_hue: str) -> tuple[Color | None, Color | None]:
        candidates: list[tuple[int, float, Color, Color]] = []
        for first in by_hue[first_hue]:
            second = lookup.get((second_hue, first.value, first.chroma))
            if second:
                candidates.append((first.chroma, first.value, first, second))
        if not candidates:
            return None, None
        _, _, first, second = max(candidates, key=lambda item: (item[0], item[1]))
        return first, second

    def equal_brightests(first_hue: str, second_hue: str) -> tuple[Color | None, Color | None]:
        # Canonical ordering makes both directions of a symmetric pair share one calculation.
        canonical = tuple(sorted((first_hue, second_hue), key=HUES.index))
        first, second = canonical_equal_brightests(*canonical)
        return (first, second) if (first_hue, second_hue) == canonical else (second, first)

    @lru_cache(maxsize=None)
    def hierarchical_brightests(superior_hue: str, inferior_hue: str) -> tuple[Color, Color | None]:
        superior = superior_brightest(superior_hue)
        for chroma in range(superior.chroma, 0, -CHROMA_STEP):
            inferior = lookup.get((inferior_hue, superior.value, chroma))
            if inferior:
                return superior, inferior
        return superior, None

    @lru_cache(maxsize=None)
    def extend(anchor: Color | None) -> Extension:
        if anchor is None:
            return Extension((), False, "neither")
        target_chroma = anchor.chroma + EXTENDED_CHROMA_STEPS * CHROMA_STEP
        # Chroma 0 reaches the neutral axis; lower values cross into the other hue.
        if target_chroma <= 0:
            return Extension((), True, "neither")
        colors: list[Color] = []
        for offset in VALUE_STEP_OFFSETS:
            value = number_key(anchor.value + offset * VALUE_STEP)
            color = lookup.get((anchor.hue, value, target_chroma))
            if color and color not in colors:
                colors.append(color)
        result = tuple(colors)
        return Extension(result, False, classify_sidedness(result, anchor.value))

    return equal_brightests, hierarchical_brightests, extend


FIELDNAMES = (
    "input_hue", "harmony", "member_offset", "member_label", "member_hue", "tonal_relationship",
    "input_anchor", "member_anchor", "generation_status", "review_required", "review_reason",
    "input_extended_count", "member_extended_count", "basic_extended_palette_count",
    "input_extension_malformed", "member_extension_malformed", "input_sidedness", "member_sidedness",
    "overall_sidedness", "is_one_sided", "input_off_black_2", "input_off_black_2_malformed",
    "input_off_black_4", "input_off_black_4_malformed", "member_off_black_2",
    "member_off_black_2_malformed", "member_off_black_4", "member_off_black_4_malformed",
)


def generate_rows(input_path: Path):
    lookup, by_hue = load_colors(input_path)
    equal_brightests, hierarchical_brightests, extend = build_validator(lookup, by_hue)
    for input_index, input_hue in enumerate(HUES):
        for harmony, members in HARMONIES:
            for offset, member_label in members:
                member_hue = HUES[(input_index + offset) % len(HUES)]
                for relationship in TONAL_RELATIONSHIPS:
                    if relationship == "equal":
                        input_anchor, member_anchor = equal_brightests(input_hue, member_hue)
                    else:
                        input_anchor, member_anchor = hierarchical_brightests(input_hue, member_hue)
                    input_extension = extend(input_anchor)
                    member_extension = extend(member_anchor)
                    reasons = []
                    if input_anchor is None:
                        reasons.append("input anchor undefined")
                    if member_anchor is None:
                        reasons.append("member anchor undefined")
                    if input_extension.malformed:
                        reasons.append("input extension crosses achromatic axis")
                    if member_extension.malformed:
                        reasons.append("member extension crosses achromatic axis")
                    input_off_blacks = {c: malformed_off_black(by_hue, input_hue, c) for c in (2, 4)}
                    member_off_blacks = {c: malformed_off_black(by_hue, member_hue, c) for c in (2, 4)}
                    overall = combine_sidedness(input_extension.sidedness, member_extension.sidedness)
                    yield {
                        "input_hue": input_hue, "harmony": harmony, "member_offset": offset,
                        "member_label": member_label, "member_hue": member_hue,
                        "tonal_relationship": relationship,
                        "input_anchor": input_anchor.name if input_anchor else "undefined",
                        "member_anchor": member_anchor.name if member_anchor else "undefined",
                        "generation_status": "review" if reasons else "ok",
                        "review_required": str(bool(reasons)).upper(), "review_reason": "; ".join(reasons),
                        "input_extended_count": len(input_extension.colors),
                        "member_extended_count": len(member_extension.colors),
                        "basic_extended_palette_count": len(input_extension.colors) + len(member_extension.colors),
                        "input_extension_malformed": str(input_extension.malformed).upper(),
                        "member_extension_malformed": str(member_extension.malformed).upper(),
                        "input_sidedness": input_extension.sidedness,
                        "member_sidedness": member_extension.sidedness, "overall_sidedness": overall,
                        "is_one_sided": str(overall in ("lighter-only", "darker-only")).upper(),
                        "input_off_black_2": input_off_blacks[2][1],
                        "input_off_black_2_malformed": str(input_off_blacks[2][0]).upper(),
                        "input_off_black_4": input_off_blacks[4][1],
                        "input_off_black_4_malformed": str(input_off_blacks[4][0]).upper(),
                        "member_off_black_2": member_off_blacks[2][1],
                        "member_off_black_2_malformed": str(member_off_blacks[2][0]).upper(),
                        "member_off_black_4": member_off_blacks[4][1],
                        "member_off_black_4_malformed": str(member_off_blacks[4][0]).upper(),
                    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = list(generate_rows(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    review_count = sum(row["review_required"] == "TRUE" for row in rows)
    print(f"Wrote {len(rows)} validation entries to {args.output}")
    print(f"Flagged {review_count} entries for review")


if __name__ == "__main__":
    main()
