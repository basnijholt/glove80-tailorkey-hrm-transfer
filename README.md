# TailorKey HRM Copier

This repository contains a small helper script (`copy_hrm_bindings.py`) that copies TailorKey's bilateral Home‑Row Mods (HRMs) from the TailorKey layout into any other Glove80 JSON layout. It was written so I could pull the Bilateral HRMs from [TailorKey](https://sites.google.com/view/keyboards/glove80_tailorkey) onto my existing `BaseModded` layer without touching the original file.

## Requirements

- Python 3.8+
- Two Glove80 layout JSON files:
  - `TailorKey v4.2h - macOS Bilateral.json` (source)
  - Your current layout (target)

## Usage

```bash
python3 copy_hrm_bindings.py \
  --source "TailorKey v4.2h - macOS Bilateral.json" \
  --target "c5342d66-e6ed-4d04-9ae0-2dfc9cd87930_QuantumTouch80.json" \
  --src-layer "HRM_macOS" \
  --dst-layer "BaseModded" \
  --value HRM_left_pinky_v1B_TKZ \
  --value HRM_left_ring_v1B_TKZ \
  --value HRM_left_middy_v1B_TKZ \
  --value HRM_left_index_v1B_TKZ
```

- The `--value` flags identify which bindings to copy; repeat for each HRM you need.
- The script writes the result to `<target_stem>_with_hrm.json` (e.g., `...QuantumTouch80_with_hrm.json`) so the original file stays untouched. Pass `--output somefile.json` to choose a different name.
- Supporting hold-tap behaviors and macros referenced by the copied HRMs are automatically pulled in to keep the layout functional.

## Next Steps

1. Flash or simulate the generated `*_with_hrm.json` layout to confirm the Bilateral HRMs behave as expected.
2. Adjust `--value` entries if you want to bring over the remaining HRMs (right-hand side, taps, etc.).
3. Once satisfied, swap the new file into your build process or replace the original layout in Git.
