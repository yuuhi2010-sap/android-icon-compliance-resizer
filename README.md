# Android Icon Compliance Resizer

[日本語版 README](README.ja.md)

Turn one icon image into Android launcher resources, Google Play Store artwork, adaptive icon XML, crop previews, and validation reports.

This is for the annoying last mile of app icon shipping: the artwork looks good, but Android launchers crop it differently, Play Store wants a separate asset, and one bad edge crop can make the app feel unfinished.

<p>
  <img src="docs/images/mieru-play-store-icon.png" alt="Generated Play Store icon" width="150">
  <img src="docs/images/mieru-preview-circle.png" alt="Circle preview" width="150">
  <img src="docs/images/mieru-preview-rounded-square.png" alt="Rounded square preview" width="150">
  <img src="docs/images/mieru-preview-squircle.png" alt="Squircle preview" width="150">
  <img src="docs/images/mieru-preview-safe-zone.png" alt="Safe zone preview" width="150">
</p>

## Why Use This?

- Avoid launcher icons that look fine as a square but get cropped on real devices.
- Generate Google Play and Android launcher assets from the same source artwork.
- Preview circle, rounded-square, squircle, square, and safe-zone masks before release.
- Use `--dry-run` and `--backup` so icon replacement is reviewable and reversible.
- Works as both a Codex Skill and a standalone Python toolkit.

## What Artwork Should I Prepare?

The easiest starting point is a large square PNG, ideally `1024x1024` or larger. Put the main symbol, logo, letter, or character in the center and leave visible padding around it. Avoid placing important details near the edges because Android launchers may crop the icon into a circle or rounded shape.

For the best Android adaptive icon result, prepare these files:

- `foreground.png`: the main logo or symbol on a transparent background.
- `background.png`: a full square background image, gradient, solid color, or simple pattern.
- `monochrome.png`: an optional single-color version for themed icons on supported Android launchers.

If you are new to app icon production, the simplest workflow is:

1. Create or export one square icon image from a design tool such as Figma, Canva, Adobe Express, Illustrator, Photoshop, Affinity Designer, or Inkscape.
2. Keep the icon simple: one clear subject, high contrast, no tiny text, and generous padding.
3. Export a PNG at `1024x1024` or `512x512`.
4. If your design tool supports layers, export the main symbol separately as a transparent `foreground.png` and the background separately as `background.png`.
5. Run this tool with `--dry-run`, then generate previews and check circle cropping before using the icon in a release.

If you only have one PNG, that is still fine. Use `--source`. This tool can create a Play Store icon and a conservative launcher icon candidate, but a single flat image cannot reliably separate the foreground from the background.

### Tips for AI-Generated Artwork

If you use an image generation tool, ask for icon-ready artwork instead of a full app icon mockup. The goal is to get clean source material that this tool can resize and validate.

Useful prompt hints:

- Ask for a centered subject on a square canvas.
- Ask for generous empty space around the subject.
- Ask for a simple, high-contrast shape that remains readable at small sizes.
- Avoid tiny text, complex scenes, thin outlines, busy backgrounds, shadows near the edge, and fake rounded app-icon frames.
- Ask for a transparent background if you want a `foreground.png`.
- Ask for a separate simple background image if your tool can generate or export layers.

Example prompt for a single PNG:

```text
Create a square 1024x1024 app icon source image for a magnifying glass camera app. Center one clear magnifying glass symbol, leave generous padding on all sides, use high contrast, simple shapes, no text, no rounded-corner frame, no drop shadow outside the artwork.
```

Example prompt for a foreground layer:

```text
Create only the foreground symbol for an Android adaptive icon: a centered magnifying glass with a small camera detail, transparent background, simple high-contrast vector-like style, generous padding, no text, no shadow, no background.
```

Example prompt for a background layer:

```text
Create only the background layer for an Android adaptive icon: square 1024x1024, calm blue-green gradient, subtle soft texture, no logo, no text, no border, no rounded corners.
```

After generating artwork, inspect it before running this tool. If the subject touches the edge, contains unreadable tiny text, or already includes rounded corners, regenerate or edit it first.

## Quick Start

Install from GitHub:

```bash
python -m pip install git+https://github.com/yuuhi2010-sap/android-icon-compliance-resizer.git
```

Or clone the repository and install dependencies:

```bash
git clone https://github.com/yuuhi2010-sap/android-icon-compliance-resizer.git
cd android-icon-compliance-resizer
python -m pip install -r requirements.txt
```

Run a dry run first:

```bash
android-icon-pack \
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
android-icon-pack \
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
android-icon-validate \
  --project-root /path/to/android-project \
  --name ic_launcher \
  --strict
```

## What It Generates

- Generates a `512x512` Google Play Store icon PNG.
- Generates Android adaptive icon foreground/background layers.
- Generates `mipmap-anydpi-v26` adaptive icon XML files.
- Optionally generates legacy density PNGs.
- Optionally generates round icon XML and previews.
- Detects non-transparent foreground bounds and fits important pixels into the Android adaptive icon safe zone.
- Renders mask previews for circle, rounded-square, squircle, square, and safe-zone overlay review.
- Validates Play icon format, adaptive XML, drawable references, legacy sizes, manifest references, and crop-risk metrics.

## Requirements

- Python 3.9 or newer
- Pillow

If you are working from a source checkout without installing the package, replace `android-icon-pack` with `python scripts/pack_android_icons.py` and `android-icon-validate` with `python scripts/validate_android_icons.py`.

## Beginner Walkthrough With Real Images

This example uses the Mieru app icon assets included in this repository. You can compare the input artwork with the generated app-store icon and launcher-mask previews before trying the tool on your own app.

### 1. Start From One Icon Image

This is the source artwork:

<img src="docs/images/mieru-source.png" alt="Mieru source icon" width="220">

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
| <img src="docs/images/mieru-foreground.png" alt="Mieru foreground" width="180"> | <img src="docs/images/mieru-background.png" alt="Mieru background" width="180"> |

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

<img src="docs/images/mieru-play-store-icon.png" alt="Generated Play Store icon" width="220">

Android launchers crop adaptive icons into different shapes depending on the device. These previews show how the same icon can look:

| Circle | Rounded square | Squircle | Safe zone |
| --- | --- | --- | --- |
| <img src="docs/images/mieru-preview-circle.png" alt="Circle preview" width="140"> | <img src="docs/images/mieru-preview-rounded-square.png" alt="Rounded square preview" width="140"> | <img src="docs/images/mieru-preview-squircle.png" alt="Squircle preview" width="140"> | <img src="docs/images/mieru-preview-safe-zone.png" alt="Safe zone preview" width="140"> |

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

## Notes

- Google Play Store icons and Android launcher icons are separate assets.
- Do not bake rounded corners, borders, or drop shadows into the Google Play icon.
- Android adaptive icon foreground content should stay inside the central safe zone.
- Always review generated previews visually before shipping.
- Run with `--dry-run` before writing to an app project.

## Project Structure

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

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for local development, test commands, and useful first contributions.
