from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import RectangleObject


ROOT = Path(__file__).resolve().parent.parent
INSPECT = ROOT / "scripts" / "inspect_pdf_artwork.py"
FROZEN = ROOT / "scripts" / "check_frozen_scope.py"
PT_PER_MM = 72 / 25.4


class SkillScriptTests(unittest.TestCase):
    def make_cover(self, path: Path) -> None:
        media_width = 191 * PT_PER_MM
        media_height = 266 * PT_PER_MM
        inset = 3 * PT_PER_MM
        writer = PdfWriter()
        page = writer.add_blank_page(width=media_width, height=media_height)
        page.cropbox = RectangleObject((0, 0, media_width, media_height))
        page.bleedbox = RectangleObject((0, 0, media_width, media_height))
        page.trimbox = RectangleObject((inset, inset, media_width - inset, media_height - inset))
        page.artbox = RectangleObject((inset, inset, media_width - inset, media_height - inset))
        writer.write(path)

    def test_pdf_geometry_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary) / "cover.pdf"
            self.make_cover(pdf)
            result = subprocess.run(
                [sys.executable, str(INSPECT), str(pdf), "--trim-mm", "185", "260", "--bleed-mm", "3"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)["valid"])

    def test_pdf_geometry_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary) / "cover.pdf"
            self.make_cover(pdf)
            result = subprocess.run(
                [sys.executable, str(INSPECT), str(pdf), "--trim-mm", "180", "250", "--bleed-mm", "3"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["valid"])

    def test_frozen_scope_detects_modified_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            (repo / "workflow").mkdir()
            (repo / "modules").mkdir()
            (repo / "modules" / "approved.jsx").write_text("approved\n", encoding="utf-8")
            (repo / "open.txt").write_text("open\n", encoding="utf-8")
            (repo / "workflow" / "MODULE_STATUS.json").write_text(json.dumps({
                "approved": {"frozen": True, "scope": ["modules/approved.jsx"]},
                "open": {"frozen": False, "scope": ["open.txt"]},
            }), encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Skill Test"], cwd=repo, check=True)
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)

            (repo / "modules" / "approved.jsx").write_text("changed\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(FROZEN), str(repo)], text=True, encoding="utf-8",
                capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["violations"][0]["path"], "modules/approved.jsx")

            subprocess.run(["git", "restore", "modules/approved.jsx"], cwd=repo, check=True)
            (repo / "open.txt").write_text("changed\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(FROZEN), str(repo)], text=True, encoding="utf-8",
                capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
