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

from hrm_utils import apply_bhrm_cleanup


def normalize_value_name(name: str) -> str:
    return name if name.startswith("&") else f"&{name}"


def load_json(path: pathlib.Path) -> dict:
    try:
        with path.open() as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        msg = f"Could not read '{path}': {exc}"
        raise SystemExit(msg) from exc


def find_layer_index(layout: dict, layer_name: str) -> int:
    try:
        return layout["layer_names"].index(layer_name)
    except ValueError as exc:
        msg = f"Layer '{layer_name}' not found. Available: {layout['layer_names']}"
        raise SystemExit(
            msg,
        ) from exc


def upsert_named(collection: list[dict], item: dict) -> None:
    for idx, existing in enumerate(collection):
        if existing.get("name") == item.get("name"):
            collection[idx] = item
            return
    collection.append(item)


def collect_layer_entries(
    layer: list[dict],
    wanted_values: list[str],
) -> list[tuple[int, dict]]:
    entries: list[tuple[int, dict]] = []
    for idx, key in enumerate(layer):
        if key.get("value") in wanted_values:
            entries.append((idx, key))
    return entries


def collect_support_objects(
    source: dict,
    names: list[str],
) -> tuple[list[dict], list[dict]]:
    holdtap_map = {item["name"]: item for item in source.get("holdTaps", [])}
    macro_map = {item["name"]: item for item in source.get("macros", [])}

    collected_holdtaps: list[dict] = []
    collected_macros: list[dict] = []
    queue: list[str] = list(names)
    seen_holdtaps: set[str] = set()
    seen_macros: set[str] = set()

    def enqueue(name: str) -> None:
        if (name in holdtap_map and name not in seen_holdtaps) or (
            name in macro_map and name not in seen_macros
        ):
            queue.append(name)

    while queue:
        name = queue.pop()
        if name in holdtap_map and name not in seen_holdtaps:
            holdtap = holdtap_map[name]
            collected_holdtaps.append(holdtap)
            seen_holdtaps.add(name)
            for binding in holdtap.get("bindings", []):
                if isinstance(binding, str):
                    enqueue(binding)
                elif isinstance(binding, dict):
                    val = binding.get("value")
                    if isinstance(val, str):
                        enqueue(val)
            continue
        if name in macro_map and name not in seen_macros:
            macro = macro_map[name]
            collected_macros.append(macro)
            seen_macros.add(name)
            for binding in macro.get("bindings", []):
                if isinstance(binding, str):
                    enqueue(binding)
                elif isinstance(binding, dict):
                    val = binding.get("value")
                    if isinstance(val, str):
                        enqueue(val)
    return collected_holdtaps, collected_macros


def collect_macro_layer_indices(macros: list[dict]) -> set[int]:
    indices: set[int] = set()
    for macro in macros:
        for binding in macro.get("bindings", []):
            if binding.get("value") != "&mo":
                continue
            for param in binding.get("params", []):
                value = param.get("value")
                if isinstance(value, int):
                    indices.add(value)
    return indices


def ensure_layers(
    source: dict,
    target: dict,
    needed_indices: set[int],
) -> dict[int, int]:
    mapping: dict[int, int] = {}
    existing = {name: idx for idx, name in enumerate(target["layer_names"])}

    for src_idx in sorted(needed_indices):
        if src_idx < 0 or src_idx >= len(source["layers"]):
            continue
        name = source["layer_names"][src_idx]
        if name in existing:
            mapping[src_idx] = existing[name]
            continue
        target["layer_names"].append(name)
        target["layers"].append(copy.deepcopy(source["layers"][src_idx]))
        new_idx = len(target["layer_names"]) - 1
        existing[name] = new_idx
        mapping[src_idx] = new_idx
    return mapping


def gather_layer_values(source: dict, layer_indices: set[int]) -> set[str]:
    values: set[str] = set()
    layers = source["layers"]
    for idx in layer_indices:
        if idx < 0 or idx >= len(layers):
            continue
        for key in layers[idx]:
            val = key.get("value")
            if isinstance(val, str):
                values.add(val)
    return values


def remap_macro_layers(macros: list[dict], layer_map: dict[int, int]) -> None:
    for macro in macros:
        for binding in macro.get("bindings", []):
            if binding.get("value") != "&mo":
                continue
            for param in binding.get("params", []):
                value = param.get("value")
                if isinstance(value, int) and value in layer_map:
                    param["value"] = layer_map[value]


def parse_args(argv: list[str]) -> argparse.Namespace:
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
        help="Behavior value to copy (repeat for multiple). Prefix '&' optional.",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. Defaults to overwriting the target path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
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
        msg = f"The following values were not found on layer '{args.src_layer}': {missing_str}"
        raise SystemExit(
            msg,
        )

    for idx, key in entries:
        dst_layer[idx] = copy.deepcopy(key)

    initial_values = {key.get("value") for _, key in entries}
    _, macros_initial = collect_support_objects(source, list(initial_values))
    required_layer_indices = collect_macro_layer_indices(macros_initial)
    layer_value_requirements = gather_layer_values(source, required_layer_indices)
    all_required_values = initial_values | layer_value_requirements

    holdtaps_src, macros_src = collect_support_objects(
        source,
        list(all_required_values),
    )

    holdtaps = [copy.deepcopy(ht) for ht in holdtaps_src]
    macros = [copy.deepcopy(m) for m in macros_src]

    required_layer_indices = collect_macro_layer_indices(macros)
    layer_index_map = ensure_layers(source, target, required_layer_indices)
    remap_macro_layers(macros, layer_index_map)

    if holdtaps:
        target.setdefault("holdTaps", [])
        for ht in holdtaps:
            upsert_named(target["holdTaps"], ht)

    if macros:
        target.setdefault("macros", [])
        for macro in macros:
            upsert_named(target["macros"], macro)

    target = apply_bhrm_cleanup(target)

    with output_path.open("w") as fh:
        json.dump(target, fh, indent=2)
        fh.write("\n")

    print(
        f"Copied {len(entries)} bindings from '{args.src_layer}' to '{args.dst_layer}' "
        f"into {output_path}.",
    )
    if holdtaps:
        print(f"Included {len(holdtaps)} holdTap definitions.")
    if macros:
        print(f"Included {len(macros)} macro definitions.")
    if layer_index_map:
        print(
            "Added/updated layers:"
            f" {', '.join(target['layer_names'][idx] for idx in layer_index_map.values())}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
