from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Pt

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/export_pptx.py"


def run_export(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True, cwd=ROOT)


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)
        self.output = self.work / "slides.pptx"

    def test_batch_native_objects_and_mixed_picture(self):
        result = run_export("examples/01-rebuilt.svg", "examples/02-mixed.svg", "-o", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        deck = Presentation(self.output)
        self.assertEqual(len(deck.slides), 2)
        self.assertEqual((deck.slide_width, deck.slide_height), (Pt(960), Pt(540)))
        header = next(s for s in deck.slides[0].shapes if s.name == "header")
        self.assertEqual(header.shapes[0].text, "客户交流准备")
        self.assertTrue(any(s.shape_type == MSO_SHAPE_TYPE.PICTURE for s in deck.slides[1].shapes))

    def test_nonzero_origin_and_letterboxing(self):
        source = self.work / "square.svg"
        source.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="10 20 200 200">'
            '<rect x="10" y="20" width="200" height="200" fill="#004488"/></svg>',
            encoding="utf-8",
        )
        result = run_export(source, "-o", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        box = Presentation(self.output).slides[0].shapes[0]
        self.assertEqual((box.left, box.top, box.width, box.height),
                         (Pt(210), Pt(0), Pt(540), Pt(540)))

    def test_invalid_later_slide_does_not_replace_existing_pptx(self):
        source = self.work / "effects.svg"
        source.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<rect width="100" height="100" fill="url(#paint)"/></svg>', encoding="utf-8",
        )
        self.output.write_bytes(b"existing edits")
        result = run_export("examples/01-rebuilt.svg", source, "-o", self.output, "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("effects.svg", result.stderr)
        self.assertEqual(self.output.read_bytes(), b"existing edits")

    def test_refuses_to_overwrite_without_force(self):
        self.output.write_bytes(b"existing edits")
        result = run_export("examples/01-rebuilt.svg", "-o", self.output)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_bytes(), b"existing edits")


if __name__ == "__main__":
    unittest.main()
