#!/usr/bin/env python3
"""Insert a dedicated HRM layer after Base and remap references accordingly."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib


def load_json(path: pathlib.Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def save_json(path: pathlib.Path, data: dict) -> None:
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def find_indices(values: list[dict], predicate) -> list[int]:
    return [idx for idx, key in enumerate(values) if predicate(key)]


def remap_layers_list(values: list[int], mapping: dict[int, int]) -> list[int]:
    new_values = []
    for val in values:
        if isinstance(val, int) and val >= 0:
            new_values.append(mapping[val])
        else:
            new_values.append(val)
    return new_values


def insert_hrm_layer(data: dict) -> dict:
    layer_names = data["layer_names"]
    layers = data["layers"]
    old_names = list(layer_names)

    try:
        base_idx = layer_names.index("Base")
        original_idx = layer_names.index("Original")
    except ValueError as exc:
        msg = "Base or Original layer missing."
        raise SystemExit(msg) from exc

    base_layer = layers[base_idx]
    original_layer = layers[original_idx]
    if len(base_layer) != len(original_layer):
        msg = "Base and Original layers differ in size."
        raise SystemExit(msg)

    hrm_positions = find_indices(
        base_layer,
        lambda key: str(key.get("value", "")).startswith("&BHRM_"),
    )

    hrm_layer = [{"value": "&trans", "params": []} for _ in base_layer]
    for idx in hrm_positions:
        hrm_layer[idx] = copy.deepcopy(base_layer[idx])
        base_layer[idx] = copy.deepcopy(original_layer[idx])

    insert_idx = base_idx + 1
    layer_names.insert(insert_idx, "HRM")
    layers.insert(insert_idx, hrm_layer)

    new_names = layer_names
    index_mapping = {
        old_idx: new_names.index(name) for old_idx, name in enumerate(old_names)
    }

    for macro in data.get("macros", []):
        for binding in macro.get("bindings", []):
            if binding.get("value") == "&mo":
                for param in binding.get("params", []):
                    val = param.get("value")
                    if isinstance(val, int):
                        param["value"] = index_mapping[val]

    def visit(obj) -> None:
        if isinstance(obj, list):
            for item in obj:
                visit(item)
        elif isinstance(obj, dict):
            if "layers" in obj and isinstance(obj["layers"], list):
                obj["layers"] = remap_layers_list(obj["layers"], index_mapping)
            for val in obj.values():
                visit(val)

    visit(data.get("holdTaps", []))
    visit(data.get("combos", []))
    visit(data.get("inputListeners", []))
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input JSON path.")
    parser.add_argument(
        "--output",
        help="Optional output JSON path (defaults to overwriting input).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path

    data = load_json(input_path)
    updated = insert_hrm_layer(data)
    save_json(output_path, updated)


if __name__ == "__main__":
    main()
