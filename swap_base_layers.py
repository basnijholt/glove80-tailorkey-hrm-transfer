#!/usr/bin/env python3
"""Swap Base/BaseModded layers while preserving key legends.

Steps:
1. Copy every Base key into BaseModded wherever BaseModded currently has &trans.
2. Replace those Base positions with &trans so Base becomes a transparent fallback.
3. Swap the layer order so BaseModded becomes layer 0 and Base layer becomes layer 1.
"""

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


def is_trans(key: dict) -> bool:
    return key.get("value") == "&trans"


def ensure_params(key: dict) -> None:
    key.setdefault("params", [])


def swap_layers(data: dict) -> dict:
    try:
        base_idx = data["layer_names"].index("Base")
        mod_idx = data["layer_names"].index("BaseModded")
    except ValueError as exc:
        msg = "Could not find Base or BaseModded layer names."
        raise SystemExit(msg) from exc

    base_layer: list[dict] = data["layers"][base_idx]
    mod_layer: list[dict] = data["layers"][mod_idx]

    if len(base_layer) != len(mod_layer):
        msg = "Base and BaseModded layers have different sizes."
        raise SystemExit(msg)

    for idx in range(len(base_layer)):
        if is_trans(mod_layer[idx]):
            mod_layer[idx] = copy.deepcopy(base_layer[idx])
            base_layer[idx] = {"value": "&trans", "params": []}
        else:
            ensure_params(mod_layer[idx])

    data["layers"][base_idx], data["layers"][mod_idx] = (
        data["layers"][mod_idx],
        data["layers"][base_idx],
    )
    data["layer_names"][base_idx], data["layer_names"][mod_idx] = (
        data["layer_names"][mod_idx],
        data["layer_names"][base_idx],
    )
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input layout JSON.")
    parser.add_argument(
        "--output",
        help="Optional output file (defaults to overwriting the input).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path
    data = load_json(input_path)
    swapped = swap_layers(data)
    save_json(output_path, swapped)


if __name__ == "__main__":
    main()
