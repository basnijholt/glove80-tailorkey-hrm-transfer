#!/usr/bin/env python3
"""Rename TailorKey HRM behavior names to a cleaner BHRM_* scheme."""

from __future__ import annotations

import argparse
import json
import pathlib

from hrm_utils import apply_bhrm_cleanup


def load_json(path: pathlib.Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def save_json(path: pathlib.Path, data: dict) -> None:
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        required=True,
        help="Layout JSON file containing HRM names.",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. Defaults to overwriting the input file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path

    data = load_json(input_path)
    updated = apply_bhrm_cleanup(data)
    save_json(output_path, updated)


if __name__ == "__main__":
    main()
