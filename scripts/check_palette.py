#!/usr/bin/env python3
"""KAN-558 brand-palette guard for the CyberFind Community theme.

This repository had no automated checks at all, which is how the colour schemes
in about.json drifted away from the brand system without anything noticing. This
script is the minimum that makes that drift visible.

It checks three things:

1.  about.json parses, declares both schemes, and every slot in each scheme
    holds exactly the canonical value.
2.  No file in the theme carries one of the retired pre-KAN-530 colours.
3.  Every hex literal in the SCSS is either a canonical palette value or one of
    the shared always-dark cross-app-header chrome hexes, which are owned by
    DESIGN.md and deliberately do not follow the scheme.

It is not a substitute for looking at the theme. Layout, spacing and the actual
rendered result still need a human in a Discourse preview.

Usage: python3 scripts/check_palette.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# design-playbook brands/cyberfind/tokens.json, published as
# @mh-cyberfind/design-artifacts v0.2.0. Hex values are the oklch round-trips
# recorded in brands/cyberfind/palette-audit.md.
EXPECTED_SCHEMES = {
    "CyberFind Light": {
        "primary": "16161D",            # text.primary
        "secondary": "FAFAFB",          # surface.canvas
        "tertiary": "312E81",           # interactive.primary — Cyber Indigo
        "quaternary": "423EA4",         # interactive.hover
        "header_background": "FFFFFF",  # surface.overlay
        "header_primary": "16161D",     # text.primary
        "highlight": "DEDDEA",          # interactive.primary at 14% over canvas
        "danger": "B31124",             # severity.high
        "success": "35781E",            # accent.evidence
        "love": "7E0C59",               # severity.critical
    },
    "CyberFind Dark": {
        "primary": "E7E8F0",
        "secondary": "0C0D14",
        "tertiary": "A5A2F5",
        "quaternary": "C1C0FF",
        "header_background": "14161F",  # dark surface.raised
        "header_primary": "E7E8F0",
        "highlight": "28283C",          # dark tertiary at 18% over canvas
        "danger": "F86A67",
        "success": "7AD560",
        "love": "E678C0",
    },
}

# The always-dark cross-app header is shared byte-for-byte with IntelHub and
# Admin. Its chrome is owned by DESIGN.md's crossAppHeader tokens and must not
# follow this theme's scheme.
CROSS_APP_HEADER_CHROME = {
    "#0a0a0a", "#27272a", "#fafafa", "#a1a1aa",
    "#18181b", "#1c1917", "#3f3f46", "#71717a",
}

# Signal Green as it appears in the logo artwork. Logo lockup only — it is not
# a UI colour in light mode (2.37:1 on the canvas).
LOGO_GREEN = {"#59ba35"}

# Colours this theme used before KAN-558 that are not in the brand system.
# Listed by value so a copy-paste revert fails loudly rather than merely
# falling outside the allow-list.
#
# #1c1917 is deliberately absent: it was the retired light scheme's `primary`
# AND it is live cross-app-header chrome, so it cannot be judged by string
# match. The about.json check and the SCSS allow-list cover both uses.
RETIRED = {
    "#c45f00", "#a35000", "#e07000", "#f08010",   # pre-KAN-530 brand orange
    "#fafaf9", "#4338ca", "#3730a3", "#9f1239",   # pre-KAN-558 light scheme
    "#16a34a", "#dc2626",
    "#e6edf3", "#0d1117", "#818cf8", "#6366f1",   # pre-KAN-558 dark scheme
    "#161b22", "#a5b4fc", "#fb7185", "#4ade80", "#f87171",
}

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")

SCSS_FILES = ["common/common.scss", "desktop/desktop.scss", "mobile/mobile.scss"]
SCANNED_FOR_RETIRED = SCSS_FILES + [
    "about.json",
    "common/header.html",
    "common/footer.html",
    "common/after_header.html",
]


def canonical_hexes() -> set[str]:
    out: set[str] = set()
    for scheme in EXPECTED_SCHEMES.values():
        out.update("#" + value.lower() for value in scheme.values())
    return out


def check_about(errors: list[str]) -> None:
    path = ROOT / "about.json"
    try:
        about = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"about.json is not readable JSON: {exc}")
        return

    schemes = about.get("color_schemes", {})
    for name, expected in EXPECTED_SCHEMES.items():
        actual = schemes.get(name)
        if actual is None:
            errors.append(f"about.json is missing the '{name}' colour scheme")
            continue
        for slot, value in expected.items():
            got = actual.get(slot)
            if got != value:
                errors.append(
                    f"about.json '{name}'.{slot} is {got!r}, expected {value!r}"
                )
        for slot in set(actual) - set(expected):
            errors.append(
                f"about.json '{name}'.{slot} is not covered by this guard — "
                "add it to EXPECTED_SCHEMES with its canonical value"
            )


def check_retired(errors: list[str]) -> None:
    for name in SCANNED_FOR_RETIRED:
        path = ROOT / name
        if not path.exists():
            continue
        lowered = path.read_text().lower()
        for hexval in sorted(RETIRED):
            if hexval in lowered:
                errors.append(f"{name} still carries the retired colour {hexval}")


def check_scss(errors: list[str]) -> None:
    allowed = canonical_hexes() | CROSS_APP_HEADER_CHROME | LOGO_GREEN
    for name in SCSS_FILES:
        path = ROOT / name
        if not path.exists():
            continue
        source = path.read_text()
        # Comments explain the chrome hexes by name; strip them before scanning.
        stripped = re.sub(r"//.*", "", source)
        found = {match.lower() for match in HEX_RE.findall(stripped)}
        for hexval in sorted(found - allowed):
            errors.append(
                f"{name} uses {hexval}, which is not in the CyberFind palette. "
                "Put the colour in about.json and resolve it through a Discourse "
                "scheme variable instead."
            )


def main() -> int:
    errors: list[str] = []
    check_about(errors)
    check_retired(errors)
    check_scss(errors)

    if errors:
        print("Brand-palette check FAILED:\n")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Brand-palette check passed.")
    print(f"  {len(EXPECTED_SCHEMES)} colour schemes verified against the canonical palette")
    print(f"  {len(SCSS_FILES)} stylesheets scanned for off-palette hex literals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
