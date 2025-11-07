# TailorKey HRM Copier

This repository contains a small helper script (`copy_hrm_bindings.py`) that copies TailorKey's bilateral Home‑Row Mods (HRMs) from the TailorKey layout into any other Glove80 JSON layout.
It was written so I could pull the Bilateral HRMs from [TailorKey](https://sites.google.com/view/keyboards/glove80_tailorkey) onto my existing `BaseModded` layer without touching the original file.

## Example input/output

- **Source layout**: [TailorKey v4.2h - macOS Bilateral](https://my.glove80.com/#/layout/user/906466c2-8029-4831-9571-2bf250ca4505)
- **Target layout**: [QuantumTouch80](https://my.glove80.com/#/layout/user/c5342d66-e6ed-4d04-9ae0-2dfc9cd87930) (to layer 1 `BaseModded`)
- **Resulting layout**: [QuantumTouch80 with BHRMs](https://my.glove80.com/#/layout/user/d39c3460-b255-4fb0-8e52-b6335e4ae94f)

## Requirements

- Python 3.8+
- Two Glove80 layout JSON files:
  - `TailorKey v4.2h - macOS Bilateral.json` (source)
  - Your current layout (target)

### Obtaining the JSON files

1. Open https://my.glove80.com/#/settings and enable **Local Backup and Restore** so the portal lets you export/import JSON layouts.
2. Visit the TailorKey download page (https://sites.google.com/view/keyboards/glove80_tailorkey/get-it-now) and follow the link to the layout you want, e.g. https://my.glove80.com/#/layout/user/906466c2-8029-4831-9571-2bf250ca4505.
3. Scroll to the bottom of that layout page, click **Export ➜ JSON Download File**, and save it as `TailorKey v4.2h - macOS Bilateral.json`.
4. Go back to your own layout on https://my.glove80.com/#/my_layouts and export it the same way; save the file alongside the TailorKey export.
5. Run `copy_hrm_bindings.py` as shown below to merge the TailorKey HRMs into your layout.

## Usage

```bash
python3 copy_hrm_bindings.py \
  --source "TailorKey v4.2h - macOS Bilateral.json" \
  --target "QuantumTouch80.json" \
  --src-layer "HRM_macOS" \
  --dst-layer "BaseModded" \
  --value HRM_left_pinky_v1B_TKZ \
  --value HRM_left_ring_v1B_TKZ \
  --value HRM_left_middy_v1B_TKZ \
  --value HRM_left_index_v1B_TKZ \
  --value HRM_right_index_v1B_TKZ \
  --value HRM_right_middy_v1B_TKZ \
  --value HRM_right_ring_v1B_TKZ \
  --value HRM_right_pinky_v1B_TKZ
```

- The `--value` flags identify which bindings to copy; repeat for each HRM you need.
- The script writes the result to `<target_stem>_with_hrm.json` (e.g., `QuantumTouch80_with_hrm.json`) so the original file stays untouched. Pass `--output somefile.json` to choose a different name.
- Supporting hold-tap behaviors and macros referenced by the copied HRMs are automatically pulled in to keep the layout functional.
- Imported behaviors are renamed to a readable `BHRM_<Hand>_<Finger>[_<Combo>][_Hold|_Tap]` scheme (e.g., `&BHRM_L_Index_Hold`) so the Glove80 editor stays tidy.
- TailorKey’s finger layers (`LeftIndex` … `RightPinky`) are copied as needed, and the macro `&mo` references are remapped so the holds activate the correct layers in your layout.

### Renaming an existing layout

If you already merged the TailorKey HRMs and just need to convert old `&HRM_*` names to the new `&BHRM_*` scheme, run:

```bash
python3 rename_hrm_names.py --input QuantumTouch80_with_hrm.json
```

Add `--output newfile.json` if you’d like to keep the original file untouched.

### One-off utilities

- `swap_base_layers.py` promotes a “modded” base layer: it copies any `&trans` bindings on `BaseModded` from the stock `Base` layer, makes those `Base` positions transparent, and swaps the two layers so your customized base becomes layer 0.
- `insert_hrm_layer.py` inserts a dedicated `HRM` layer (right after `Base` by default), moves all `&BHRM_*` bindings there, restores the original tap behavior on `Base`, and remaps every `&mo` / `layers` reference so indices stay correct. Use this if you want HRMs only when you momentarily switch into that layer.

## Importing the merged layout

1. Return to https://my.glove80.com/#/layout/<your-layout>.
2. Scroll to the bottom-left “Local Backup and Restore” card where it shows `No file chosen` and the “Drag and drop file here, or click to select” area.
3. Choose the newly generated `*_with_hrm.json` file, click **Import**, then hit **Build** and flash the resulting firmware as usual.

## Next Steps

1. Flash or simulate the generated `*_with_hrm.json` layout to confirm the Bilateral HRMs behave as expected.
2. Adjust `--value` entries if you want to bring over the remaining HRMs (right-hand side, taps, etc.).
3. Once satisfied, swap the new file into your build process or replace the original layout in Git.
