#!/usr/bin/env python3
"""Copy Home-Row Mod (HRM) bindings plus supporting objects between Glove80 layout JSON files.

Example:
    python3 copy_hrm_bindings.py \
        --source "TailorKey v4.2h - macOS Bilateral.json" \
        --target "c5342d66-e6ed-4d04-9ae0-2dfc9cd87930_QuantumTouch80.json" \
        --src-layer "HRM_macOS" \
        --dst-layer "BaseModded" \
        --value HRM_left_pinky_v1B_TKZ \
        --value HRM_left_ring_v1B_TKZ \
        --value HRM_left_middy_v1B_TKZ \
        --value HRM_left_index_v1B_TKZ \
        --output "QuantumTouch80_with_tailorkey_hrm.json"

If --output is omitted the script writes to <target_stem>_with_hrm<suffix>.
"""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
from typing import Dict, List, Tuple


def load_json(path: pathlib.Path) -> Dict:
    try:
        with path.open() as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise SystemExit(f"Could not read '{path}': {exc}") from exc


def find_layer_index(layout: Dict, layer_name: str) -> int:
    try:
        return layout["layer_names"].index(layer_name)
    except ValueError as exc:
        raise SystemExit(
            f"Layer '{layer_name}' not found. Available: {layout['layer_names']}"
        ) from exc


def normalize_value_name(name: str) -> str:
    return name if name.startswith("&") else f"&{name}"


def upsert_named(collection: List[Dict], item: Dict) -> None:
    for idx, existing in enumerate(collection):
        if existing.get("name") == item.get("name"):
            collection[idx] = item
            return
    collection.append(item)


def collect_layer_entries(
    layer: List[Dict], wanted_values: List[str]
) -> List[Tuple[int, Dict]]:
    entries: List[Tuple[int, Dict]] = []
    for idx, key in enumerate(layer):
        if key.get("value") in wanted_values:
            entries.append((idx, key))
    return entries


def collect_support_objects(
    source: Dict, names: List[str]
) -> Tuple[List[Dict], List[Dict]]:
    holdtap_map = {item["name"]: item for item in source.get("holdTaps", [])}
    macro_map = {item["name"]: item for item in source.get("macros", [])}

    collected_holdtaps: List[Dict] = []
    collected_macros: List[Dict] = []

    for name in names:
        holdtap = holdtap_map.get(name)
        if not holdtap:
            continue
        collected_holdtaps.append(holdtap)
        for binding_name in holdtap.get("bindings", []):
            if not isinstance(binding_name, str):
                continue
            macro = macro_map.get(binding_name)
            if macro:
                collected_macros.append(macro)
    return collected_holdtaps, collected_macros


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Source layout JSON path.")
    parser.add_argument("--target", required=True, help="Target layout JSON path.")
    parser.add_argument(
        "--src-layer",
        required=True,
        help="Layer name in the source layout to pull bindings from.",
    )
    parser.add_argument(
        "--dst-layer",
        required=True,
        help="Layer name in the target layout to update.",
    )
    parser.add_argument(
        "--value",
        dest="values",
        action="append",
        required=True,
        help="Behavior value to copy (repeat for multiple). "
        "Prefix '&' optional.",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. Defaults to overwriting the target path.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    source_path = pathlib.Path(args.source)
    target_path = pathlib.Path(args.target)
    if args.output:
        output_path = pathlib.Path(args.output)
    else:
        suffix = target_path.suffix or ".json"
        output_path = target_path.with_name(f"{target_path.stem}_with_hrm{suffix}")

    source = load_json(source_path)
    target = load_json(target_path)

    src_layer_idx = find_layer_index(source, args.src_layer)
    dst_layer_idx = find_layer_index(target, args.dst_layer)

    src_layer = source["layers"][src_layer_idx]
    dst_layer = target["layers"][dst_layer_idx]

    wanted_values = [normalize_value_name(v) for v in args.values]
    entries = collect_layer_entries(src_layer, wanted_values)
    missing = set(wanted_values) - {key.get("value") for _, key in entries}
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise SystemExit(
            f"The following values were not found on layer '{args.src_layer}': {missing_str}"
        )

    for idx, key in entries:
        dst_layer[idx] = copy.deepcopy(key)

    holdtaps, macros = collect_support_objects(
        source, [key.get("value") for _, key in entries]
    )

    if holdtaps:
        target.setdefault("holdTaps", [])
        for ht in holdtaps:
            upsert_named(target["holdTaps"], copy.deepcopy(ht))

    if macros:
        target.setdefault("macros", [])
        for macro in macros:
            upsert_named(target["macros"], copy.deepcopy(macro))

    with output_path.open("w") as fh:
        json.dump(target, fh, indent=2)
        fh.write("\n")

    print(
        f"Copied {len(entries)} bindings from '{args.src_layer}' to '{args.dst_layer}' "
        f"into {output_path}."
    )
    if holdtaps:
        print(f"Included {len(holdtaps)} holdTap definitions.")
    if macros:
        print(f"Included {len(macros)} macro definitions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
