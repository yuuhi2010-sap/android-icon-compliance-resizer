# Android Icon Compliance Resizer

[日本語版 README](README.ja.md)

Android Icon Compliance Resizer is a Codex Skill and script toolkit for converting existing icon artwork into Android launcher icon resources and Google Play Store icon assets.

It does not create a new icon design. Instead, it preserves supplied artwork as much as possible while resizing, centering, padding, generating adaptive icon XML, producing previews, and checking for cropping risk.

## What It Does

- Generates a `512x512` Google Play Store icon PNG.
- Generates Android adaptive icon foreground/background layers.
- Generates `mipmap-anydpi-v26` adaptive icon XML files.
- Optionally generates legacy density PNGs.
- Optionally generates round icon XML and previews.
- Detects non-transparent foreground bounds and fits important pixels into the Android adaptive icon safe zone.
- Renders mask previews for circle, rounded-square, squircle, square, and safe-zone overlay review.
- Validates Play icon format, adaptive XML, drawable references, legacy sizes, manifest references, and crop-risk metrics.

## Included Files

```text
android-icon-compliance-resizer/
├── SKILL.md
├── requirements.txt
├── scripts/
│   ├── pack_android_icons.py
│   ├── validate_android_icons.py
│   └── generate_icon_previews.py
├── references/
│   └── android_icon_requirements.md
└── examples/
    └── README.md
```

## Requirements

- Python 3.9 or newer
- Pillow

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Quick Start

Run a dry run first:

```bash
python scripts/pack_android_icons.py \
  --project-root /path/to/android-project \
  --source /path/to/icon.png \
  --name ic_launcher \
  --legacy \
  --adaptive \
  --round \
  --preview \
  --dry-run
```

Generate files with backups:

```bash
python scripts/pack_android_icons.py \
  --project-root /path/to/android-project \
  --source /path/to/icon.png \
  --name ic_launcher \
  --legacy \
  --adaptive \
  --round \
  --preview \
  --backup
```

Validate generated resources:

```bash
python scripts/validate_android_icons.py \
  --project-root /path/to/android-project \
  --name ic_launcher \
  --strict
```

## Better Adaptive Icons

For best results, provide separated layers:

```bash
python scripts/pack_android_icons.py \
  --project-root /path/to/android-project \
  --foreground /path/to/foreground.png \
  --background "#0F172A" \
  --monochrome /path/to/monochrome.png \
  --name ic_launcher \
  --adaptive \
  --round \
  --preview \
  --backup
```

A single flat PNG can be used, but it cannot reliably separate the logo from the background. In that case, treat the adaptive icon output as a conservative candidate and inspect the generated previews before release.

## Repository Description

Short description for GitHub:

```text
Codex Skill and Python toolkit for resizing, packing, previewing, and validating Android launcher icons and Google Play Store icons.
```

Suggested topics:

```text
android, adaptive-icons, launcher-icon, google-play, python, pillow, codex-skill
```

## Notes

- Google Play Store icons and Android launcher icons are separate assets.
- Do not bake rounded corners, borders, or drop shadows into the Google Play icon.
- Android adaptive icon foreground content should stay inside the central safe zone.
- Always review generated previews visually before shipping.
- Run with `--dry-run` before writing to an app project.

