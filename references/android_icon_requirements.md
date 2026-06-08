# Android / Google Play Icon Requirements

This reference separates Google Play Store listing icons from Android launcher icons. Use official documentation first when requirements may have changed.

## Official Sources Checked

- Android Developers: Adaptive icons
  - https://developer.android.com/develop/ui/compose/system/icon_design_adaptive?hl=ja
  - Notes checked on 2026-06-06: adaptive icons use foreground/background layers, optional monochrome layer, `108x108dp` layers, a centered `66x66dp` safe zone, and manifest `android:icon` / optional `android:roundIcon`.
- Android Developers: Google Play icon design specifications
  - https://developer.android.com/distribute/google-play/resources/icon-design-specifications
  - Notes checked on 2026-06-06: Play icon final asset is `512x512`, `32-bit PNG`, `sRGB`, max `1024KB`, full square, no baked drop shadow, and Google Play dynamically applies the rounded mask and shadow. The current page says the dynamic corner radius is equivalent to 30% of icon size.
- Play Console Help: Add preview assets to showcase your app
  - https://support.google.com/googleplay/android-developer/answer/9866151
  - Notes checked on 2026-06-06: the Play app icon is required for store listings and does not replace the Android launcher icon.
- Play Console Help: Metadata policy
  - https://support.google.com/googleplay/android-developer/answer/9898842
  - Notes checked on 2026-06-06: app title, icon, and developer name must not imply store performance/ranking, price/promotional information, or Google Play program relationship.

## Google Play Store Icon

- Purpose: store listing, search results, charts, and other Google Play surfaces.
- Must be `512x512` PNG.
- Must be 32-bit PNG, with alpha.
- Must be sRGB.
- Must be no larger than `1024KB`.
- Treat as a full square asset.
- Do not bake in outer rounded corners.
- Do not bake in outer drop shadows.
- Google Play dynamically applies its own rounded mask and shadow.
- Do not include badges or text that suggest ranking, price, categories, Google Play program participation, or other misleading claims.
- Automated detection of misleading text, badges, edge shadows, and rounded corners is incomplete; keep these as manual review checklist items.

## Android Adaptive Icon

- Purpose: Android launcher and system surfaces.
- Adaptive Icon is a layered drawable, normally with:
  - `foreground`
  - `background`
  - optional `monochrome` for themed icons
- The XML form is:

```xml
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
    <monochrome android:drawable="@drawable/ic_launcher_monochrome" />
</adaptive-icon>
```

- Store adaptive XML in `res/mipmap-anydpi-v26/<name>.xml`.
- Store the referenced bitmap layers in `res/drawable` or `res/drawable-nodpi`.
- Each layer represents a `108x108dp` canvas.
- This Skill uses a `432x432px` image canvas as a high-resolution stand-in for `108x108dp`.
- Android launcher masks vary by device and launcher.
- Keep important visible foreground content in the centered `66/108` safe-zone ratio by default.
- On a `432x432px` canvas, the default safe zone is `264x264px`.
- Background and non-essential decorative bleed can extend to the full canvas.
- Important logos, letters, faces, and symbols should stay inside the safe zone.
- Avoid masks or background shadows around the icon edge.

## Round Icon

- `android:roundIcon` is optional but used by launchers that represent apps with circular icons.
- Use `res/mipmap-anydpi-v26/<name>_round.xml` for adaptive round icon XML when generating round output.
- Validate circle masks because round icons crop edge content more aggressively.
- Report outside-mask foreground pixels and ratios.

## Legacy Launcher PNG Sizes

Generate these only when legacy PNGs are requested or the project still needs them:

- `mipmap-mdpi`: `48x48`
- `mipmap-hdpi`: `72x72`
- `mipmap-xhdpi`: `96x96`
- `mipmap-xxhdpi`: `144x144`
- `mipmap-xxxhdpi`: `192x192`

## Skill Policy

- Do not redesign icons.
- Preserve the supplied artwork and make mechanical compliance adjustments only.
- If foreground/background are not separated, warn that Adaptive Icon quality cannot be guaranteed.
- Always create previews for visual confirmation when possible.
- Always validate before release use.
