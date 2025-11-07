"""Shared helpers for renaming TailorKey HRM bindings and improving descriptions."""

from __future__ import annotations

import re
from typing import Any

HAND_MAP = {"left": "L", "right": "R"}
HAND_NAMES = {"L": "Left", "R": "Right"}
FINGER_MAP = {
    "index": "Index",
    "middle": "Middle",
    "middy": "Middle",
    "ring": "Ring",
    "ringy": "Ring",
    "pinky": "Pinky",
}
ROLE_MAP = {"hold": "Hold", "tap": "Tap"}
HRM_PATTERN = re.compile(r"&HRM_[A-Za-z0-9_]+")


def normalize_base(name: str) -> str:
    return re.sub(r"_v[0-9A-Za-z]*(_TKZ)?$", "", name)


def clean_token(token: str) -> str:
    token = token.lower()
    token = token.replace("tkz", "")
    token = re.sub(r"v\d+$", "", token)
    token = re.sub(r"\d+$", "", token)
    return token.strip("_")


def format_token(token: str) -> str:
    token = clean_token(token)
    if not token:
        return ""
    return FINGER_MAP.get(token, token.capitalize())


def rename_hrm(value: str) -> str:
    if not value.startswith("&HRM_"):
        return value

    body = normalize_base(value[1:])
    parts = body.split("_")
    if len(parts) < 3 or parts[0] != "HRM":
        return value

    hand = HAND_MAP.get(parts[1].lower())
    if not hand:
        return value

    tokens = [format_token(token) for token in parts[2:]]
    tokens = [token for token in tokens if token]
    if not tokens:
        return value

    extras: list[str] = []
    role = None
    for token in tokens[1:]:
        token_lower = token.lower()
        if token_lower in ROLE_MAP and role is None:
            role = ROLE_MAP[token_lower]
        else:
            extras.append(token)

    primary = tokens[0]
    new_name = f"&BHRM_{hand}_{primary}"
    if extras:
        new_name += "_" + "_".join(extras)
    if role:
        new_name += f"_{role}"
    return new_name


def canonicalize_bhrm(value: str) -> str:
    if not value.startswith("&BHRM_"):
        return value
    tokens = value[6:].split("_")
    if not tokens:
        return value
    hand = tokens[0].upper()
    rest = tokens[1:]
    if not rest:
        return value
    role = None
    if rest[-1].lower() in ROLE_MAP:
        role = ROLE_MAP[rest[-1].lower()]
        rest = rest[:-1]
    cleaned = [format_token(token) for token in rest]
    cleaned = [token for token in cleaned if token]
    if not cleaned:
        return value
    new_name = f"&BHRM_{hand}_{cleaned[0]}"
    if len(cleaned) > 1:
        new_name += "_" + "_".join(cleaned[1:])
    if role:
        new_name += f"_{role}"
    return new_name


def rename_in_text(text: str) -> str:
    return HRM_PATTERN.sub(lambda match: rename_hrm(match.group()), text)


def transform_strings(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: transform_strings(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [transform_strings(item) for item in obj]
    if isinstance(obj, str):
        if obj.startswith("&BHRM_"):
            return canonicalize_bhrm(obj)
        if obj.startswith("&HRM_"):
            return rename_hrm(obj)
        if "HRM_" in obj:
            return rename_in_text(obj)
        return obj.replace(" - TailorKey", "").strip()
    return obj


def parse_bhrm_name(name: str) -> dict[str, Any] | None:
    if not name.startswith("&BHRM_"):
        return None
    tokens = name[6:].split("_")
    if not tokens:
        return None
    hand_key = tokens[0].upper()
    hand = HAND_NAMES.get(hand_key)
    if not hand:
        return None
    rest = tokens[1:]
    if not rest:
        return None
    role = None
    if rest[-1] in ("Hold", "Tap"):
        role = rest[-1]
        rest = rest[:-1]
    if not rest:
        return None
    primary = rest[0]
    combos = rest[1:]
    return {
        "hand": hand,
        "primary": primary,
        "combos": combos,
        "role": role,
    }


def describe_macro(name: str, current: str) -> str:
    info = parse_bhrm_name(name)
    base = current.replace(" - TailorKey", "").strip()
    if not info:
        return base
    hand = info["hand"]
    finger = info["primary"]
    if info["role"] == "Hold":
        return f"Hold: activate {hand} {finger} layer"
    if info["role"] == "Tap":
        return "Tap: restore base key"
    return base


def describe_holdtap(name: str, current: str) -> str:
    info = parse_bhrm_name(name)
    base = current.replace(" - TailorKey", "").strip()
    if not info:
        return base
    finger = info["primary"]
    combos = info["combos"]
    if combos:
        combo_text = " + ".join([finger, *combos])
        return f"Combo: {combo_text}"
    return "HRM: tap→key, hold→layer"


def apply_bhrm_cleanup(data: dict[str, Any]) -> dict[str, Any]:
    cleaned = transform_strings(data)
    macros = cleaned.get("macros", [])
    for macro in macros:
        macro["description"] = describe_macro(
            macro.get("name", ""),
            macro.get("description", ""),
        )
    holdtaps = cleaned.get("holdTaps", [])
    for holdtap in holdtaps:
        holdtap["description"] = describe_holdtap(
            holdtap.get("name", ""),
            holdtap.get("description", ""),
        )
    macros.sort(key=lambda m: m.get("name", ""))
    holdtaps.sort(key=lambda ht: ht.get("name", ""))
    return cleaned
