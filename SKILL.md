---
name: android-icon-compliance-resizer
description: 既存のアイコン素材をAndroidランチャーアイコン、丸型アイコン、Adaptive Icon、Google Play Store掲載用アイコンの仕様に合わせてリサイズ・配置・XML生成・検証するSkill。新しいデザインは作らず、見切れ防止のために前景画像のbounds検出、安全領域へのスケール調整、複数マスクでのはみ出し検証、プレビュー生成を行う。ユーザーが「ストアアイコン」「アプリのホーム画面アイコン」「丸型アイコン」「adaptive icon」「launcher icon」「Google Play icon」「アイコンが見切れる」「mipmap」「AndroidManifestのアイコン設定」などを依頼したときに使う。
---

# Android Icon Compliance Resizer

Use this Skill to adapt existing Android / Google Play icon artwork to the expected output sizes, resource locations, adaptive icon XML, manifest references, previews, and verification checks. Do not create a new icon design. Preserve the supplied artwork as much as possible while resizing, centering, padding, and warning about risks.

## Core Rules

- Do not design new icon artwork.
- Treat Google Play Store icons and Android home screen launcher icons as separate assets.
- Prefer separated `foreground`, `background`, and `monochrome` inputs when available.
- If only one image is provided, generate a Google Play icon and a conservative Android foreground candidate, but warn that automatic foreground/background separation is not guaranteed.
- Detect the foreground image's non-transparent pixel bounds and fit important visible content into the center safe zone.
- Use the foreground bounds and, where possible, alpha-weighted visual centroid to center the artwork.
- Keep important logos, letters, faces, and symbols inside the central `66/108` safe-zone ratio by default.
- Allow background and bleed-only decoration to fill the full `108/108` canvas.
- Preview and validate circle, rounded-square, squircle, and square masks.
- Warn whenever cutoff risk remains.
- Update `AndroidManifest.xml` only when requested, using XML parsing and preserving the Android namespace.
- Before overwriting existing files, prefer `--dry-run`, review planned changes, and use `--backup`; require `--force` for overwrites.

## Asset Types

### Google Play Store Icon

- Store listing asset, not a replacement for the launcher icon.
- Output as `512x512` PNG, 32-bit PNG with alpha where possible, sRGB-equivalent, max `1024KB`.
- Treat as a full square asset.
- Do not bake in rounded corners, outer border, or drop shadow; Google Play applies masking and shadows dynamically.
- Automated ranking, price, category, Google Play program badge, or misleading text detection is unreliable; report it as a manual checklist warning.

### Android Home Screen Icon

- Launcher asset used by Android launchers and app surfaces.
- Generate Adaptive Icon XML with `foreground` and `background`; include `monochrome` when supplied.
- Generate legacy density PNGs when requested.
- Fit important foreground pixels inside the central `66/108` safe-zone ratio.

### Round Icon

- Referenced by `android:roundIcon`.
- Generate `ic_launcher_round.xml` when round output is enabled.
- Always preview and validate the circle mask because it is more likely to crop edge content.
- Report circle-mask outside pixels and ratio.

## Workflow

1. Detect the project type:
   - Native Android/Kotlin/Java: look for `AndroidManifest.xml`, `app/build.gradle`, `app/build.gradle.kts`, `src/main/res`.
   - Flutter: look for `pubspec.yaml`, `android/app/src/main`.
   - React Native: look for `package.json`, `android/app/src/main`.
   - Expo: look for `app.json`, `app.config.js`, `app.config.ts`, `expo`.
   - Capacitor: look for `capacitor.config.*`, `android/app/src/main`.
2. Find icon-related files:
   - `AndroidManifest.xml`
   - `res/mipmap-*`
   - `res/drawable*`
   - `manifest.json`
   - `app.json`
   - `app.config.js`
   - `capacitor.config.*`
3. Inspect the input artwork. Prefer separated `--foreground`, `--background`, and `--monochrome`.
4. If only `--source` is supplied:
   - Use it to generate the Google Play Store icon.
   - Use it as a foreground candidate for Android outputs.
   - Warn that a single PNG cannot reliably separate background and logo layers.
   - Recommend providing separated foreground/background assets before relying on Adaptive Icon output.
5. Run `scripts/pack_android_icons.py` first, normally with `--dry-run` before writing:
   - Detect foreground alpha bounds.
   - If the input lacks alpha, treat the full image as bounds and warn.
   - Scale and center important foreground pixels into the safe zone.
   - Create `512x512` Google Play PNG.
   - Create `432x432` foreground/background/monochrome drawable PNG layers.
   - Create `res/mipmap-anydpi-v26/<name>.xml` and `<name>_round.xml`.
   - Create density legacy PNGs when `--legacy` is set.
   - Update `AndroidManifest.xml` only when `--update-manifest` is set.
6. Run `scripts/generate_icon_previews.py` or pass `--preview`:
   - Generate `circle`, `rounded-square`, `squircle`, `square`, and `safe-zone-overlay` preview PNGs.
   - Generate `index.html` for side-by-side review where possible.
7. Run `scripts/validate_android_icons.py`:
   - Check Play icon format, size, and file size.
   - Check legacy density PNG sizes.
   - Check adaptive XML and referenced drawables.
   - Check manifest icon and roundIcon references.
   - Check foreground safe-zone fit.
   - Check mask outside-pixel counts and ratios.
8. Report:
   - Files changed or planned.
   - Warnings and errors.
   - Whether the single-source limitation applies.
   - Preview paths that the user should inspect visually.
   - Next checks before using the assets in a real release.

## Bundled Scripts

- `scripts/pack_android_icons.py`: pack existing artwork into Android and Google Play icon outputs.
- `scripts/validate_android_icons.py`: validate generated icon resources and mask cutoff risk.
- `scripts/generate_icon_previews.py`: render launcher-mask preview images and an HTML index.

Install dependencies when needed:

```bash
python -m pip install -r .agents/skills/android-icon-compliance-resizer/requirements.txt
```

## Typical Commands

Dry-run a single PNG:

```bash
python .agents/skills/android-icon-compliance-resizer/scripts/pack_android_icons.py --project-root . --source ./icon.png --dry-run
```

Generate separated adaptive resources:

```bash
python .agents/skills/android-icon-compliance-resizer/scripts/pack_android_icons.py --project-root . --foreground ./foreground.png --background "#0F172A" --monochrome ./monochrome.png --name ic_launcher --legacy --adaptive --round --preview --backup
```

Validate strictly:

```bash
python .agents/skills/android-icon-compliance-resizer/scripts/validate_android_icons.py --project-root . --name ic_launcher --strict
```

## Reference

Read `references/android_icon_requirements.md` when exact Android / Google Play icon requirements are needed, especially if Play Console behavior or official dimensions may have changed.
