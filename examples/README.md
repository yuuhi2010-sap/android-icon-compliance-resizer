# Android Icon Compliance Resizer Examples

## 例1: 単一PNGから生成

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

## 例2: foreground/backgroundを分けて生成

```bash
python scripts/pack_android_icons.py \
  --project-root /path/to/android-project \
  --foreground /path/to/foreground.png \
  --background "#0F172A" \
  --monochrome /path/to/monochrome.png \
  --name ic_launcher \
  --update-manifest \
  --preview \
  --backup
```

## 例3: dry-run

```bash
python scripts/pack_android_icons.py \
  --project-root . \
  --source ./icon.png \
  --dry-run
```

## 例4: 検証

```bash
python scripts/validate_android_icons.py \
  --project-root . \
  --name ic_launcher \
  --strict
```

## 例5: プレビューのみ生成

```bash
python scripts/generate_icon_previews.py \
  --project-root . \
  --name ic_launcher
```
