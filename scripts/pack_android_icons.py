#!/usr/bin/env python3
"""Pack existing artwork into Android and Google Play compliant icon resources."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional, Tuple


CANVAS_SIZE = 432
PLAY_SIZE = 512
ANDROID_NS = "http://schemas.android.com/apk/res/android"
LEGACY_SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}


class IconToolError(RuntimeError):
    pass


class WritePlan:
    def __init__(self, dry_run: bool, force: bool, backup: bool) -> None:
        self.dry_run = dry_run
        self.force = force
        self.backup = backup
        self.changed: list[Path] = []
        self.planned: list[Path] = []
        self.warnings: list[str] = []

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"WARNING: {message}")

    def write_bytes(self, path: Path, data: bytes) -> None:
        self._prepare(path)
        self.planned.append(path)
        if self.dry_run:
            print(f"DRY-RUN: write {path}")
            return
        path.write_bytes(data)
        self.changed.append(path)

    def save_image(self, image, path: Path) -> None:
        self._prepare(path)
        self.planned.append(path)
        if self.dry_run:
            print(f"DRY-RUN: save image {path} size={image.size}")
            return
        image.save(path)
        self.changed.append(path)

    def write_text(self, path: Path, text: str) -> None:
        self._prepare(path)
        self.planned.append(path)
        if self.dry_run:
            print(f"DRY-RUN: write text {path}")
            return
        path.write_text(text, encoding="utf-8")
        self.changed.append(path)

    def _prepare(self, path: Path) -> None:
        if path.exists():
            if self.dry_run:
                print(f"DRY-RUN: existing file would be replaced {path}")
            elif not self.force and not self.backup:
                raise IconToolError(
                    f"既存ファイルがあります: {path}\n"
                    "対処: --dry-runで確認するか、--backup または --force を指定してください。"
                )
            elif self.backup:
                timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
                backup_path = path.with_name(f"{path.name}.{timestamp}.bak")
                shutil.copy2(path, backup_path)
                self.changed.append(backup_path)
                print(f"Backup: {backup_path}")
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            print(f"DRY-RUN: ensure directory {path.parent}")


def import_pillow():
    try:
        from PIL import Image, ImageChops, ImageDraw, ImageOps
    except ImportError as exc:
        raise IconToolError(
            "Pillowが見つかりません。`python -m pip install -r requirements.txt` を実行してください。"
        ) from exc
    return Image, ImageChops, ImageDraw, ImageOps


def detect_project(project_root: Path) -> list[str]:
    markers = []
    if (project_root / "pubspec.yaml").is_file():
        markers.append("Flutter")
    if (project_root / "package.json").is_file() and (project_root / "android").is_dir():
        markers.append("React Native / Expo候補")
    if any((project_root / name).is_file() for name in ("app.json", "app.config.js", "app.config.ts")):
        markers.append("Expo候補")
    if any(project_root.glob("capacitor.config.*")):
        markers.append("Capacitor")
    if (project_root / "app" / "build.gradle").is_file() or (project_root / "app" / "build.gradle.kts").is_file():
        markers.append("Native Android/Gradle")
    return markers or ["Android構成を自動判定中"]


def find_android_main(project_root: Path) -> Path:
    candidates = [
        project_root / "app" / "src" / "main",
        project_root / "android" / "app" / "src" / "main",
        project_root / "src" / "main",
        project_root,
    ]
    for candidate in candidates:
        if (candidate / "res").is_dir() or (candidate / "AndroidManifest.xml").is_file():
            return candidate
    fallback = project_root / "app" / "src" / "main"
    print(f"INFO: Android resが未作成のようです。標準候補を使います: {fallback}")
    return fallback


def default_play_store_output(project_root: Path) -> Path:
    fastlane = project_root / "fastlane" / "metadata" / "android" / "en-US" / "images"
    if fastlane.exists():
        return fastlane / "icon.png"
    return project_root / "play-store" / "icon.png"


def load_image(path: Path):
    Image, _, _, _ = import_pillow()
    if not path.is_file():
        raise IconToolError(f"画像ファイルが見つかりません: {path}")
    try:
        with Image.open(path) as image:
            if "A" not in image.getbands():
                print(f"WARNING: alphaチャンネルがないため、画像全体を重要boundsとして扱います: {path}")
            return image.convert("RGBA")
    except OSError as exc:
        raise IconToolError(f"画像ファイルを開けません: {path}\n原因: {exc}") from exc


def parse_color(value: str) -> Tuple[int, int, int, int]:
    text = value.strip()
    if not text.startswith("#"):
        raise IconToolError(f"単色指定は #RRGGBB または #AARRGGBB 形式にしてください: {value}")
    hex_value = text[1:]
    if len(hex_value) == 6:
        r, g, b = int(hex_value[0:2], 16), int(hex_value[2:4], 16), int(hex_value[4:6], 16)
        return r, g, b, 255
    if len(hex_value) == 8:
        a, r, g, b = (
            int(hex_value[0:2], 16),
            int(hex_value[2:4], 16),
            int(hex_value[4:6], 16),
            int(hex_value[6:8], 16),
        )
        return r, g, b, a
    raise IconToolError(f"単色指定は #RRGGBB または #AARRGGBB 形式にしてください: {value}")


def alpha_bounds(image) -> Optional[Tuple[int, int, int, int]]:
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    alpha = image.getchannel("A")
    return alpha.getbbox()


def alpha_centroid(image, bounds: Tuple[int, int, int, int]) -> Tuple[float, float]:
    alpha = image.getchannel("A")
    pixels = alpha.load()
    total = 0.0
    sx = 0.0
    sy = 0.0
    left, top, right, bottom = bounds
    for y in range(top, bottom):
        for x in range(left, right):
            weight = pixels[x, y]
            if weight:
                total += weight
                sx += x * weight
                sy += y * weight
    if total == 0:
        return ((left + right) / 2.0, (top + bottom) / 2.0)
    return (sx / total, sy / total)


def fit_foreground_to_safe_zone(image, safe_zone_ratio: float, size: int = CANVAS_SIZE):
    Image, _, _, _ = import_pillow()
    image = image.convert("RGBA")
    bounds = alpha_bounds(image)
    if bounds is None:
        raise IconToolError("foreground/source画像に不透明ピクセルがありません。")
    left, top, right, bottom = bounds
    cropped = image.crop(bounds)
    width = max(1, right - left)
    height = max(1, bottom - top)
    safe = int(round(size * safe_zone_ratio))
    scale = min(safe / width, safe / height, 1.0 if max(width, height) <= safe else safe / max(width, height))
    target_width = max(1, int(round(width * scale)))
    target_height = max(1, int(round(height * scale)))
    resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)

    original_centroid = alpha_centroid(image, bounds)
    center_offset_x = original_centroid[0] - ((left + right) / 2.0)
    center_offset_y = original_centroid[1] - ((top + bottom) / 2.0)
    adjusted_x = (size - target_width) / 2.0 - center_offset_x * scale * 0.35
    adjusted_y = (size - target_height) / 2.0 - center_offset_y * scale * 0.35
    safe_left = (size - safe) / 2.0
    safe_top = (size - safe) / 2.0
    adjusted_x = max(safe_left, min(adjusted_x, safe_left + safe - target_width))
    adjusted_y = max(safe_top, min(adjusted_y, safe_top + safe - target_height))

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(resized, (int(round(adjusted_x)), int(round(adjusted_y))))
    return canvas


def make_background(background: Optional[str], source_image=None, size: int = CANVAS_SIZE):
    Image, _, _, _ = import_pillow()
    if background is None:
        return Image.new("RGBA", (size, size), (255, 255, 255, 255))
    if background.startswith("#"):
        return Image.new("RGBA", (size, size), parse_color(background))
    bg = load_image(Path(background).expanduser().resolve())
    return ImageOps_fit(bg, (size, size))


def ImageOps_fit(image, size: Tuple[int, int]):
    Image, _, _, ImageOps = import_pillow()
    return ImageOps.fit(image.convert("RGBA"), size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def make_play_icon(source, safe_zone_ratio: float):
    Image, _, _, ImageOps = import_pillow()
    image = source.convert("RGBA")
    if image.size == (PLAY_SIZE, PLAY_SIZE):
        result = image
    else:
        result = ImageOps.contain(image, (PLAY_SIZE, PLAY_SIZE), method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (PLAY_SIZE, PLAY_SIZE), (0, 0, 0, 0))
        canvas.alpha_composite(result, ((PLAY_SIZE - result.width) // 2, (PLAY_SIZE - result.height) // 2))
        result = canvas
    return result


def make_monochrome(image, color=(255, 255, 255, 255)):
    Image, _, _, _ = import_pillow()
    image = image.convert("RGBA")
    alpha = image.getchannel("A")
    mono = Image.new("RGBA", image.size, color)
    mono.putalpha(alpha)
    return mono


def adaptive_xml(name: str, include_monochrome: bool) -> str:
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">',
        f'    <background android:drawable="@drawable/{name}_background" />',
        f'    <foreground android:drawable="@drawable/{name}_foreground" />',
    ]
    if include_monochrome:
        lines.append(f'    <monochrome android:drawable="@drawable/{name}_monochrome" />')
    lines.append("</adaptive-icon>")
    return "\n".join(lines) + "\n"


def update_manifest(manifest_path: Path, name: str, plan: WritePlan) -> None:
    import xml.etree.ElementTree as ET

    if not manifest_path.is_file():
        raise IconToolError(
            f"AndroidManifest.xmlが見つかりません: {manifest_path}\n"
            "対処: --project-root を確認するか、manifestを作成後に再実行してください。"
        )
    ET.register_namespace("android", ANDROID_NS)
    try:
        tree = ET.parse(manifest_path)
    except ET.ParseError as exc:
        raise IconToolError(f"AndroidManifest.xmlをXMLとして解析できません: {manifest_path}\n原因: {exc}") from exc
    root = tree.getroot()
    application = root.find("application")
    if application is None:
        raise IconToolError(f"AndroidManifest.xmlにapplicationタグがありません: {manifest_path}")
    icon_key = f"{{{ANDROID_NS}}}icon"
    round_key = f"{{{ANDROID_NS}}}roundIcon"
    before_icon = application.attrib.get(icon_key)
    before_round = application.attrib.get(round_key)
    application.set(icon_key, f"@mipmap/{name}")
    application.set(round_key, f"@mipmap/{name}_round")
    print(f"Manifest android:icon: {before_icon} -> @mipmap/{name}")
    print(f"Manifest android:roundIcon: {before_round} -> @mipmap/{name}_round")
    if plan.dry_run:
        plan.planned.append(manifest_path)
        print(f"DRY-RUN: update manifest {manifest_path}")
        return
    plan._prepare(manifest_path)
    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)
    plan.changed.append(manifest_path)


def optimize_png_if_needed(path: Path, plan: WritePlan) -> None:
    if plan.dry_run or not path.exists() or path.stat().st_size <= 1024 * 1024:
        return
    Image, _, _, _ = import_pillow()
    with Image.open(path) as image:
        image.save(path, optimize=True)
    if path.stat().st_size > 1024 * 1024:
        plan.warn(f"Google Play用アイコンが1024KBを超えています: {path} ({path.stat().st_size} bytes)")


def run_preview(project_root: Path, name: str, foreground_path: Path, background_path: Path, dry_run: bool) -> None:
    if dry_run:
        print("DRY-RUN: preview generation skipped")
        return
    script = Path(__file__).with_name("generate_icon_previews.py")
    command = [
        sys.executable,
        str(script),
        "--project-root",
        str(project_root),
        "--name",
        name,
        "--foreground",
        str(foreground_path),
        "--background",
        str(background_path),
    ]
    subprocess.run(command, check=False)


def pack_icons(args) -> WritePlan:
    Image, _, _, _ = import_pillow()
    project_root = Path(args.project_root).resolve()
    main_dir = find_android_main(project_root)
    res_dir = main_dir / "res"
    drawable_dir = res_dir / "drawable-nodpi"
    mipmap_anydpi = res_dir / "mipmap-anydpi-v26"
    plan = WritePlan(args.dry_run, args.force, args.backup)

    print("Detected project type: " + ", ".join(detect_project(project_root)))
    if args.source and (args.foreground or args.background):
        plan.warn("--source と foreground/background が同時指定されています。Adaptive出力はforeground/backgroundを優先します。")
    if not args.source and not args.foreground:
        raise IconToolError("--source または --foreground を指定してください。")

    source_image = load_image(Path(args.source).expanduser().resolve()) if args.source else None
    foreground_input = load_image(Path(args.foreground).expanduser().resolve()) if args.foreground else source_image
    if foreground_input is None:
        raise IconToolError("foreground候補を決定できません。")
    if args.source and not args.foreground:
        plan.warn("単一画像入力のため、背景とロゴの完全な分離は保証できません。分離済みforeground/background素材の提供を推奨します。")

    foreground = fit_foreground_to_safe_zone(foreground_input, args.safe_zone_ratio)
    background = make_background(args.background, source_image)
    monochrome = None
    if args.monochrome:
        monochrome = fit_foreground_to_safe_zone(load_image(Path(args.monochrome).expanduser().resolve()), args.safe_zone_ratio)
    elif args.auto_monochrome:
        monochrome = make_monochrome(foreground)
        plan.warn("monochromeをalpha maskベースの単色シルエットとして自動生成しました。品質は手動確認してください。")

    play_source = source_image or foreground_input
    play_icon = make_play_icon(play_source, args.safe_zone_ratio)
    play_output = Path(args.play_store_output).resolve() if args.play_store_output else default_play_store_output(project_root)
    plan.save_image(play_icon, play_output)
    optimize_png_if_needed(play_output, plan)

    fg_path = drawable_dir / f"{args.name}_foreground.png"
    bg_path = drawable_dir / f"{args.name}_background.png"
    mono_path = drawable_dir / f"{args.name}_monochrome.png"
    plan.save_image(foreground, fg_path)
    plan.save_image(background, bg_path)
    if monochrome is not None:
        plan.save_image(monochrome, mono_path)

    if args.legacy:
        combined = background.copy()
        combined.alpha_composite(foreground)
        for directory_name, size in LEGACY_SIZES.items():
            legacy = combined.resize((size, size), Image.Resampling.LANCZOS)
            plan.save_image(legacy, res_dir / directory_name / f"{args.name}.png")

    if args.adaptive:
        xml = adaptive_xml(args.name, monochrome is not None)
        plan.write_text(mipmap_anydpi / f"{args.name}.xml", xml)
        if args.round:
            plan.write_text(mipmap_anydpi / f"{args.name}_round.xml", xml)

    if args.update_manifest:
        update_manifest(main_dir / "AndroidManifest.xml", args.name, plan)

    print("Manual checklist: Google Play用アイコンに角丸、外枠、外側ドロップシャドウを焼き込んでいないか確認してください。")
    print("Manual checklist: ランキング、価格、カテゴリ、Google Play実績/プログラムを示すバッジや誤認テキストがないか確認してください。")

    if args.preview:
        run_preview(project_root, args.name, fg_path, bg_path, args.dry_run)

    print("Planned files:")
    for path in plan.planned:
        print(f"  {path}")
    if not args.dry_run:
        print("Changed files:")
        for path in plan.changed:
            print(f"  {path}")
        print("Next: validate_android_icons.py を実行し、生成されたプレビューを目視確認してください。")
    else:
        print("DRY-RUN完了: ファイルは書き込んでいません。")
    return plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resize, place, generate, and validate existing Android / Google Play icon artwork without redesigning it."
    )
    parser.add_argument("--project-root", default=".", help="Target project root. Defaults to current directory.")
    parser.add_argument("--source", help="Single source icon image when layers are not separated.")
    parser.add_argument("--foreground", help="Adaptive Icon foreground image.")
    parser.add_argument("--background", help='Adaptive Icon background image path or color, for example "#0F172A".')
    parser.add_argument("--monochrome", help="Android themed icon monochrome foreground image.")
    parser.add_argument("--auto-monochrome", action="store_true", help="Generate a simple alpha-mask monochrome silhouette.")
    parser.add_argument("--name", default="ic_launcher", help="Output icon resource name. Defaults to ic_launcher.")
    parser.add_argument("--play-store-output", help="Google Play 512x512 icon output path.")
    parser.add_argument("--safe-zone-ratio", type=float, default=66 / 108, help="Safe-zone ratio. Defaults to 66/108.")
    parser.add_argument("--legacy", action="store_true", help="Generate mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi legacy PNGs.")
    parser.add_argument("--adaptive", action=argparse.BooleanOptionalAction, default=True, help="Generate adaptive icon XML. Enabled by default.")
    parser.add_argument("--round", action=argparse.BooleanOptionalAction, default=True, help="Generate round adaptive icon XML. Enabled by default.")
    parser.add_argument("--update-manifest", action="store_true", help="Update AndroidManifest.xml android:icon and android:roundIcon.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without writing files.")
    parser.add_argument("--force", action="store_true", help="Allow overwriting existing files.")
    parser.add_argument("--backup", action="store_true", help="Create timestamped .bak files before overwriting.")
    parser.add_argument("--preview", action="store_true", help="Generate mask previews after writing resources.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        pack_icons(args)
        return 0
    except IconToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
