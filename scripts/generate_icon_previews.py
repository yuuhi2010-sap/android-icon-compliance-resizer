#!/usr/bin/env python3
"""Generate Android adaptive icon mask previews."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple


CANVAS_SIZE = 432
ANDROID_NS = "http://schemas.android.com/apk/res/android"


class IconToolError(RuntimeError):
    pass


def import_pillow():
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise IconToolError(
            "Pillowが見つかりません。`python -m pip install -r requirements.txt` を実行してください。"
        ) from exc
    return Image, ImageDraw


def log(message: str) -> None:
    print(message)


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
    raise IconToolError(
        f"Androidのresディレクトリが見つかりません: {project_root}\n"
        "対処: --project-root にAndroidモジュールまたはプロジェクトルートを指定してください。"
    )


def resource_to_path(main_dir: Path, reference: str) -> Optional[Path]:
    if not reference.startswith("@"):
        return None
    try:
        res_type, name = reference[1:].split("/", 1)
    except ValueError:
        return None
    res_root = main_dir / "res"
    if res_type in {"drawable", "mipmap"}:
        for directory in sorted(res_root.glob(f"{res_type}*")):
            for extension in (".png", ".webp", ".jpg", ".jpeg", ".xml"):
                candidate = directory / f"{name}{extension}"
                if candidate.is_file():
                    return candidate
    return None


def parse_adaptive_xml(xml_path: Path) -> Dict[str, str]:
    import xml.etree.ElementTree as ET

    if not xml_path.is_file():
        raise IconToolError(f"Adaptive Icon XMLが見つかりません: {xml_path}")
    root = ET.parse(xml_path).getroot()
    result: Dict[str, str] = {}
    for tag in ("background", "foreground", "monochrome"):
        node = root.find(tag)
        if node is not None:
            value = node.attrib.get(f"{{{ANDROID_NS}}}drawable")
            if value:
                result[tag] = value
    if "background" not in result or "foreground" not in result:
        raise IconToolError(f"XMLにbackground/foreground参照がありません: {xml_path}")
    return result


def load_layer(path: Path, size: int = CANVAS_SIZE):
    Image, _ = import_pillow()
    with Image.open(path) as image:
        return image.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)


def load_background(value: str, main_dir: Path, size: int = CANVAS_SIZE):
    Image, _ = import_pillow()
    if value.startswith("#"):
        return Image.new("RGBA", (size, size), value)
    path = resource_to_path(main_dir, value) if value.startswith("@") else Path(value)
    if path is None or not path.is_file():
        raise IconToolError(f"background画像が見つかりません: {value}")
    return load_layer(path, size)


def make_mask(kind: str, size: int = CANVAS_SIZE):
    Image, ImageDraw = import_pillow()
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    if kind == "circle":
        draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    elif kind == "rounded-square":
        radius = int(size * 0.222)
        draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    elif kind == "square":
        draw.rectangle((0, 0, size, size), fill=255)
    elif kind == "squircle":
        pixels = mask.load()
        center = (size - 1) / 2.0
        radius = size / 2.0
        power = 4.0
        for y in range(size):
            ny = abs((y - center) / radius)
            for x in range(size):
                nx = abs((x - center) / radius)
                if (nx**power + ny**power) <= 1.0:
                    pixels[x, y] = 255
    else:
        raise IconToolError(f"未対応のマスクです: {kind}")
    return mask


def compose(background, foreground):
    image = background.copy()
    image.alpha_composite(foreground)
    return image


def apply_mask(image, mask):
    result = image.copy()
    result.putalpha(mask)
    return result


def draw_safe_zone_overlay(image, safe_zone_ratio: float):
    _, ImageDraw = import_pillow()
    result = image.copy()
    draw = ImageDraw.Draw(result, "RGBA")
    size = result.size[0]
    safe = int(round(size * safe_zone_ratio))
    margin = (size - safe) // 2
    draw.rectangle((0, 0, size - 1, size - 1), outline=(60, 130, 255, 220), width=4)
    draw.rectangle(
        (margin, margin, size - margin - 1, size - margin - 1),
        outline=(255, 70, 70, 230),
        width=4,
    )
    draw.line((size // 2, 0, size // 2, size), fill=(255, 255, 255, 160), width=2)
    draw.line((0, size // 2, size, size // 2), fill=(255, 255, 255, 160), width=2)
    return result


def write_html_index(output_dir: Path, files: Iterable[Path]) -> Path:
    cards = []
    for path in files:
        rel = path.name
        cards.append(
            f'<figure><img src="{rel}" alt="{path.stem}"><figcaption>{path.stem}</figcaption></figure>'
        )
    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Android Icon Previews</title>
<style>
body{font-family:system-ui,sans-serif;margin:24px;background:#f6f7f9;color:#1f2937}
.grid{display:flex;flex-wrap:wrap;gap:18px}
figure{margin:0;padding:12px;background:#fff;border:1px solid #d7dce2;border-radius:8px}
img{width:216px;height:216px;image-rendering:auto;background:#e5e7eb}
figcaption{text-align:center;margin-top:8px;font-size:14px}
</style>
</head>
<body>
<h1>Android Icon Previews</h1>
<div class="grid">
""" + "\n".join(cards) + """
</div>
</body>
</html>
"""
    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


def find_layer_paths(project_root: Path, name: str) -> Tuple[Path, Path]:
    main_dir = find_android_main(project_root)
    xml_path = main_dir / "res" / "mipmap-anydpi-v26" / f"{name}.xml"
    refs = parse_adaptive_xml(xml_path)
    background_path = resource_to_path(main_dir, refs["background"])
    foreground_path = resource_to_path(main_dir, refs["foreground"])
    if background_path is None or not background_path.is_file():
        raise IconToolError(f"background参照先が見つかりません: {refs['background']}")
    if foreground_path is None or not foreground_path.is_file():
        raise IconToolError(f"foreground参照先が見つかりません: {refs['foreground']}")
    return background_path, foreground_path


def generate_previews(
    project_root: Path,
    name: str,
    output_dir: Path,
    foreground: Optional[Path] = None,
    background: Optional[str] = None,
    safe_zone_ratio: float = 66 / 108,
) -> list[Path]:
    Image, _ = import_pillow()
    main_dir = find_android_main(project_root)
    if foreground is None or background is None:
        bg_path, fg_path = find_layer_paths(project_root, name)
        foreground = foreground or fg_path
        background = background or str(bg_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    bg = load_background(background, main_dir)
    fg = load_layer(foreground)
    combined = compose(bg, fg)

    written: list[Path] = []
    for mask_name in ("circle", "rounded-square", "squircle", "square"):
        preview = apply_mask(combined, make_mask(mask_name))
        path = output_dir / f"{name}_{mask_name}.png"
        preview.save(path)
        written.append(path)

    overlay_path = output_dir / f"{name}_safe-zone-overlay.png"
    draw_safe_zone_overlay(combined, safe_zone_ratio).save(overlay_path)
    written.append(overlay_path)
    written.append(write_html_index(output_dir, written))
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Android adaptive icon previews for circle, rounded-square, squircle, square, and safe-zone overlay."
    )
    parser.add_argument("--project-root", default=".", help="Android project root. Defaults to current directory.")
    parser.add_argument("--name", default="ic_launcher", help="Icon resource base name. Defaults to ic_launcher.")
    parser.add_argument("--foreground", help="Optional foreground image path. Defaults to adaptive XML foreground.")
    parser.add_argument("--background", help="Optional background image path or color. Defaults to adaptive XML background.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Preview output directory. Defaults to build/icon-previews under project root.",
    )
    parser.add_argument(
        "--safe-zone-ratio",
        type=float,
        default=66 / 108,
        help="Safe-zone ratio for overlay. Defaults to 66/108.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        project_root = Path(args.project_root).resolve()
        output_dir = Path(args.output_dir).resolve() if args.output_dir else project_root / "build" / "icon-previews"
        written = generate_previews(
            project_root=project_root,
            name=args.name,
            output_dir=output_dir,
            foreground=Path(args.foreground).resolve() if args.foreground else None,
            background=args.background,
            safe_zone_ratio=args.safe_zone_ratio,
        )
        log("Preview files:")
        for path in written:
            log(f"  {path}")
        return 0
    except IconToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
