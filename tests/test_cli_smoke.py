from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - exercised only when dev dependencies are missing.
    Image = None
    ImageDraw = None


ROOT = Path(__file__).resolve().parents[1]


class CliSmokeTest(unittest.TestCase):
    @unittest.skipIf(Image is None or ImageDraw is None, "Pillow is required for icon smoke tests")
    def test_pack_preview_and_validate_native_android_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            main_dir = project_root / "app" / "src" / "main"
            main_dir.mkdir(parents=True)
            (main_dir / "AndroidManifest.xml").write_text(
                '<manifest xmlns:android="http://schemas.android.com/apk/res/android" />',
                encoding="utf-8",
            )

            source_icon = project_root / "source.png"
            self._write_source_icon(source_icon)

            pack_result = self._run(
                "scripts/pack_android_icons.py",
                "--project-root",
                str(project_root),
                "--source",
                str(source_icon),
                "--name",
                "ic_launcher_test",
                "--legacy",
                "--preview",
            )
            self.assertEqual(pack_result.returncode, 0, pack_result.stdout + pack_result.stderr)

            validate_result = self._run(
                "scripts/validate_android_icons.py",
                "--project-root",
                str(project_root),
                "--name",
                "ic_launcher_test",
                "--json",
            )
            self.assertEqual(validate_result.returncode, 0, validate_result.stdout + validate_result.stderr)
            self.assertIn("adaptive icon XML found", validate_result.stdout)

            preview_dir = project_root / "build" / "icon-previews"
            self.assertTrue((preview_dir / "ic_launcher_test_circle.png").is_file())
            self.assertTrue((project_root / "play-store" / "icon.png").is_file())

    def test_entry_points_import(self) -> None:
        import scripts.generate_icon_previews
        import scripts.pack_android_icons
        import scripts.validate_android_icons

        self.assertTrue(callable(scripts.pack_android_icons.main))
        self.assertTrue(callable(scripts.validate_android_icons.main))
        self.assertTrue(callable(scripts.generate_icon_previews.main))

    def _run(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / script), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def _write_source_icon(self, path: Path) -> None:
        image = Image.new("RGBA", (1024, 1024), "#0F766E")
        draw = ImageDraw.Draw(image)
        draw.ellipse((270, 220, 660, 610), fill="#ECFEFF")
        draw.ellipse((340, 290, 590, 540), fill="#0F766E")
        draw.rounded_rectangle((610, 610, 800, 720), radius=45, fill="#ECFEFF")
        image.save(path)


if __name__ == "__main__":
    unittest.main()
