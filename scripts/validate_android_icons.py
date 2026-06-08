#!/usr/bin/env python3
"""Validate Android and Google Play icon resources."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple


CANVAS_SIZE = 432
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


@dataclass
class Finding:
    level: str
    message: str
    detail: Optional[dict] = None


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def info(self, message: str, detail: Optional[dict] = None) -> None:
        self.findings.append(Finding("info", message, detail))

    def warning(self, message: str, detail: Optional[dict] = None) -> None:
        self.findings.append(Finding("warning", message, detail))

    def error(self, message: str, detail: Optional[dict] = None) -> None:
        self.findings.append(Finding("error", message, detail))

    @property
    def has_warnings(self) -> bool:
        return any(item.level == "warning" for item in self.findings)

    @property
    def has_errors(self) -> bool:
        return any(item.level == "error" for item in self.findings)

    def to_json(self) -> str:
        return json.dumps(
            [{"level": item.level, "message": item.message, "detail": item.detail} for item in self.findings],
            ensure_ascii=False,
            indent=2,
        )


def import_pillow():
    try:
        from PIL import Image, ImageChops, ImageDraw
    except ImportError as exc:
        raise IconToolError(
            "Pillowが見つかりません。`python -m pip install -r requirements.txt` を実行してください。"
        ) from exc
    return Image, ImageChops, ImageDraw


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
        f"AndroidManifest.xmlまたはresディレクトリが見つかりません: {project_root}\n"
        "対処: --project-root にAndroidプロジェクトまたはAndroidモジュールを指定してください。"
    )


def find_play_icon(project_root: Path) -> Optional[Path]:
    candidates = [
        project_root / "play-store" / "icon.png",
        project_root / "fastlane" / "metadata" / "android" / "en-US" / "images" / "icon.png",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def resource_to_path(main_dir: Path, reference: str) -> Optional[Path]:
    if not reference or not reference.startswith("@"):
        return None
    try:
        res_type, name = reference[1:].split("/", 1)
    except ValueError:
        return None
    for directory in sorted((main_dir / "res").glob(f"{res_type}*")):
        for extension in (".png", ".webp", ".jpg", ".jpeg", ".xml"):
            candidate = directory / f"{name}{extension}"
            if candidate.is_file():
                return candidate
    return None


def parse_adaptive_xml(xml_path: Path, report: Report) -> Dict[str, str]:
    import xml.etree.ElementTree as ET

    refs: Dict[str, str] = {}
    if not xml_path.is_file():
        report.error(f"Adaptive Icon XMLがありません: {xml_path}")
        return refs
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        report.error(f"Adaptive Icon XMLを解析できません: {xml_path}", {"error": str(exc)})
        return refs
    if root.tag.split("}")[-1] != "adaptive-icon":
        report.error(f"ルート要素がadaptive-iconではありません: {xml_path}")
        return refs
    for tag in ("background", "foreground", "monochrome"):
        node = root.find(tag)
        if node is not None:
            value = node.attrib.get(f"{{{ANDROID_NS}}}drawable")
            if value:
                refs[tag] = value
    if "background" not in refs:
        report.error(f"Adaptive Icon XMLにbackground参照がありません: {xml_path}")
    if "foreground" not in refs:
        report.error(f"Adaptive Icon XMLにforeground参照がありません: {xml_path}")
    return refs


def alpha_bounds(image) -> Optional[Tuple[int, int, int, int]]:
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    alpha = image.getchannel("A")
    return alpha.getbbox()


def mask_for(kind: str, size: int):
    Image, _, ImageDraw = import_pillow()
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    if kind == "circle":
        draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    elif kind == "rounded-square":
        draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * 0.222), fill=255)
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


def count_mask_overflow(foreground, mask) -> Tuple[int, int, float]:
    if foreground.mode != "RGBA":
        foreground = foreground.convert("RGBA")
    alpha = foreground.getchannel("A")
    alpha_pixels = alpha.load()
    mask_pixels = mask.load()
    total = 0
    outside = 0
    width, height = foreground.size
    for y in range(height):
        for x in range(width):
            if alpha_pixels[x, y] > 0:
                total += 1
                if mask_pixels[x, y] == 0:
                    outside += 1
    ratio = outside / total if total else 0.0
    return outside, total, ratio


def validate_play_icon(project_root: Path, report: Report) -> None:
    Image, _, _ = import_pillow()
    path = find_play_icon(project_root)
    if path is None:
        report.warning("Google Play用アイコンが見つかりません。候補: play-store/icon.png または fastlane/metadata/android/en-US/images/icon.png")
        return
    try:
        with Image.open(path) as image:
            if image.format != "PNG":
                report.error(f"Google Play用アイコンがPNGではありません: {path}", {"format": image.format})
            if image.size != (512, 512):
                report.error(f"Google Play用アイコンが512x512ではありません: {path}", {"size": image.size})
            if image.mode not in {"RGBA", "LA", "P"}:
                report.warning(f"Google Play用アイコンが32-bit PNG相当か確認してください: {path}", {"mode": image.mode})
            if image.info.get("icc_profile") is None:
                report.warning("Google Play用アイコンのsRGB判定は完全ではありません。ICCプロファイルがないため、sRGB相当として手動確認してください。")
    except OSError as exc:
        report.error(f"Google Play用アイコンを開けません: {path}", {"error": str(exc)})
        return
    size = path.stat().st_size
    if size > 1024 * 1024:
        report.error(f"Google Play用アイコンが1024KBを超えています: {path}", {"bytes": size})
    report.warning("手動確認: Google Play用アイコンに外側の角丸、外枠、ドロップシャドウを焼き込んでいないか確認してください。")
    report.warning("手動確認: ランキング、価格、カテゴリ、Google Play上の実績やプログラム参加を示すバッジ/誤認テキストがないか確認してください。")


def validate_legacy(main_dir: Path, name: str, report: Report) -> None:
    Image, _, _ = import_pillow()
    for directory_name, expected_size in LEGACY_SIZES.items():
        path = main_dir / "res" / directory_name / f"{name}.png"
        if not path.is_file():
            report.warning(f"レガシーPNGがありません: {path}")
            continue
        try:
            with Image.open(path) as image:
                if image.size != (expected_size, expected_size):
                    report.error(
                        f"{directory_name} のサイズが正しくありません: {path}",
                        {"expected": [expected_size, expected_size], "actual": list(image.size)},
                    )
        except OSError as exc:
            report.error(f"レガシーPNGを開けません: {path}", {"error": str(exc)})


def validate_manifest(main_dir: Path, name: str, report: Report) -> None:
    import xml.etree.ElementTree as ET

    manifest_path = main_dir / "AndroidManifest.xml"
    if not manifest_path.is_file():
        report.warning(f"AndroidManifest.xmlが見つかりません: {manifest_path}")
        return
    try:
        root = ET.parse(manifest_path).getroot()
    except ET.ParseError as exc:
        report.error(f"AndroidManifest.xmlを解析できません: {manifest_path}", {"error": str(exc)})
        return
    application = root.find("application")
    if application is None:
        report.error(f"AndroidManifest.xmlにapplicationタグがありません: {manifest_path}")
        return
    icon = application.attrib.get(f"{{{ANDROID_NS}}}icon")
    round_icon = application.attrib.get(f"{{{ANDROID_NS}}}roundIcon")
    expected_icon = f"@mipmap/{name}"
    expected_round = f"@mipmap/{name}_round"
    if icon != expected_icon:
        report.warning("AndroidManifest.xmlのandroid:iconが期待値と異なります。", {"actual": icon, "expected": expected_icon})
    if round_icon != expected_round:
        report.warning("AndroidManifest.xmlのandroid:roundIconが期待値と異なります。", {"actual": round_icon, "expected": expected_round})


def validate_foreground(main_dir: Path, foreground_path: Path, safe_zone_ratio: float, report: Report) -> None:
    Image, _, _ = import_pillow()
    try:
        with Image.open(foreground_path) as opened:
            image = opened.convert("RGBA").resize((CANVAS_SIZE, CANVAS_SIZE), Image.Resampling.LANCZOS)
    except OSError as exc:
        report.error(f"foreground画像を開けません: {foreground_path}", {"error": str(exc)})
        return
    bounds = alpha_bounds(image)
    if bounds is None:
        report.error(f"foreground画像に不透明ピクセルがありません: {foreground_path}")
        return
    safe = int(round(CANVAS_SIZE * safe_zone_ratio))
    left = (CANVAS_SIZE - safe) // 2
    top = (CANVAS_SIZE - safe) // 2
    right = left + safe
    bottom = top + safe
    over = {
        "left": max(0, left - bounds[0]),
        "top": max(0, top - bounds[1]),
        "right": max(0, bounds[2] - right),
        "bottom": max(0, bounds[3] - bottom),
    }
    if any(over.values()):
        report.error("foregroundの不透明boundsが安全領域からはみ出しています。", {"bounds": bounds, "safe_zone": [left, top, right, bottom], "overflow_px": over})
    else:
        report.info("foregroundの不透明boundsは安全領域内です。", {"bounds": bounds, "safe_zone": [left, top, right, bottom]})

    for mask_name in ("circle", "rounded-square", "squircle", "square"):
        outside, total, ratio = count_mask_overflow(image, mask_for(mask_name, CANVAS_SIZE))
        detail = {"outside_pixels": outside, "opaque_pixels": total, "ratio": ratio}
        if ratio >= 0.01:
            report.error(f"{mask_name}マスク外の不透明ピクセルが1%以上あります。", detail)
        elif ratio >= 0.001:
            report.warning(f"{mask_name}マスク外の不透明ピクセルが0.1%以上あります。", detail)
        else:
            report.info(f"{mask_name}マスク外はみ出しは許容範囲です。", detail)


def validate_adaptive(main_dir: Path, name: str, safe_zone_ratio: float, report: Report) -> None:
    xml_path = main_dir / "res" / "mipmap-anydpi-v26" / f"{name}.xml"
    round_xml_path = main_dir / "res" / "mipmap-anydpi-v26" / f"{name}_round.xml"
    refs = parse_adaptive_xml(xml_path, report)
    if round_xml_path.is_file():
        parse_adaptive_xml(round_xml_path, report)
    else:
        report.warning(f"丸型Adaptive Icon XMLがありません: {round_xml_path}")
    for key, value in refs.items():
        path = resource_to_path(main_dir, value)
        if path is None:
            report.error(f"{key}参照先が見つかりません: {value}")
        else:
            report.info(f"{key}参照先を確認しました: {path}")
    foreground_ref = refs.get("foreground")
    foreground_path = resource_to_path(main_dir, foreground_ref) if foreground_ref else None
    if foreground_path is not None:
        validate_foreground(main_dir, foreground_path, safe_zone_ratio, report)


def validate(project_root: Path, name: str, safe_zone_ratio: float) -> Report:
    report = Report()
    main_dir = find_android_main(project_root)
    validate_play_icon(project_root, report)
    validate_legacy(main_dir, name, report)
    validate_adaptive(main_dir, name, safe_zone_ratio, report)
    validate_manifest(main_dir, name, report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Android launcher, round, adaptive, and Google Play Store icons.")
    parser.add_argument("--project-root", default=".", help="Android project root. Defaults to current directory.")
    parser.add_argument("--name", default="ic_launcher", help="Icon resource base name. Defaults to ic_launcher.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--safe-zone-ratio", type=float, default=66 / 108, help="Foreground safe-zone ratio. Defaults to 66/108.")
    parser.add_argument("--preview-dir", help="Reserved for preview artifact checks. Currently reports generated resource state.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = validate(Path(args.project_root).resolve(), args.name, args.safe_zone_ratio)
    except IconToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(report.to_json())
    else:
        for finding in report.findings:
            detail = f" {finding.detail}" if finding.detail else ""
            print(f"{finding.level.upper()}: {finding.message}{detail}")

    if report.has_errors:
        return 1
    if args.strict and report.has_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
