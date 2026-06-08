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

## Beginner Walkthrough With Real Images

This example uses the Mieru app icon assets included in this repository. You can compare the input artwork with the generated app-store icon and launcher-mask previews before trying the tool on your own app.

### 1. Start From One Icon Image

This is the source artwork:

![Mieru source icon](docs/images/mieru-source.png)

If you only have one PNG, use `--source`. The tool can still create a Play Store icon and a conservative Android launcher candidate.

```bash
python scripts/pack_android_icons.py \
  --project-root /path/to/android-project \
  --source docs/images/mieru-source.png \
  --name ic_launcher \
  --legacy \
  --adaptive \
  --round \
  --preview \
  --dry-run
```

`--dry-run` means "show what would be created, but do not write files yet." Beginners should run this first.

### 2. Use Separate Layers When You Have Them

Adaptive icons work better when the foreground and background are separate.

| Foreground | Background |
| --- | --- |
| ![Mieru foreground](docs/images/mieru-foreground.png) | ![Mieru background](docs/images/mieru-background.png) |

Generate the icon resources:

```bash
python scripts/pack_android_icons.py \
  --project-root /path/to/android-project \
  --foreground docs/images/mieru-foreground.png \
  --background docs/images/mieru-background.png \
  --name ic_launcher \
  --legacy \
  --adaptive \
  --round \
  --preview \
  --backup
```

`--backup` keeps a backup before replacing existing icon files.

### 3. Check What Was Created

The Google Play Store icon is a square `512x512` PNG:

![Generated Play Store icon](docs/images/mieru-play-store-icon.png)

Android launchers crop adaptive icons into different shapes depending on the device. These previews show how the same icon can look:

| Circle | Rounded square | Squircle | Safe zone |
| --- | --- | --- | --- |
| ![Circle preview](docs/images/mieru-preview-circle.png) | ![Rounded square preview](docs/images/mieru-preview-rounded-square.png) | ![Squircle preview](docs/images/mieru-preview-squircle.png) | ![Safe zone preview](docs/images/mieru-preview-safe-zone.png) |

If important parts of the icon touch the red safe-zone guide or disappear in the circle preview, adjust the source artwork or provide a foreground layer with more padding.

### 4. Validate Before Release

After generating icons, run:

```bash
python scripts/validate_android_icons.py \
  --project-root /path/to/android-project \
  --name ic_launcher \
  --strict
```

If validation reports warnings, read them before uploading to Google Play or shipping the app.

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
