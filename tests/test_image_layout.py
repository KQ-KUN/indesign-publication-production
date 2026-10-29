from __future__ import annotations

import copy
import importlib.util
import math
from pathlib import Path
import random
import tempfile
import unittest

from PIL import Image

SPEC = importlib.util.spec_from_file_location("image_layout", Path(__file__).parents[1]/"scripts/image_layout.py")
layout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(layout)


def image(ident, ratio, **kwargs):
    return {"id": ident, "width_px": 1200*ratio, "height_px": 1200, **kwargs}


def request(*images, **kwargs):
    return {"column_width": 73, "available_height": 150, "gap": 3, "images": list(images), **kwargs}


def native_fixture(plan):
    # Synthetic observations for validator unit tests. Real host evidence is tested separately.
    return {"origin": "InDesign_DOM", "units": "mm", "items": [
        {"image_id": f["image_id"], "frame": {k: f[k] for k in ("x", "y", "width", "height")},
         "graphic": dict(f["graphic"]), "page_id": 1, "rotation": 0, "shear": 0}
        for f in plan["frames"]], "captions": [
            {"frame": {k: c[k] for k in ("x", "y", "width", "height")}, "text": c["text"],
             "image_ids": c["image_ids"], "overflows": False, "page_id": 1} for c in plan["captions"]]}


class ImageLayoutTests(unittest.TestCase):
    def test_A_single_landscape_fills_column(self):
        p = layout.calculate(request(image("a", 2)))
        f = p["frames"][0]
        self.assertEqual(p["layout_mode"], "SINGLE_LANDSCAPE")
        self.assertAlmostEqual(f["width"], 73)
        self.assertAlmostEqual(f["x"], 0)
        self.assertAlmostEqual(f["height"], 36.5)
        self.assertTrue(layout.validate_geometry(p, native_fixture(p))["valid"])

    def test_B_single_portrait_two_thirds_centered(self):
        p = layout.calculate(request(image("p", .6), x=11))
        f = p["frames"][0]
        self.assertEqual(p["layout_mode"], "SINGLE_PORTRAIT")
        self.assertAlmostEqual(f["width"], 73*2/3, places=5)
        self.assertAlmostEqual(f["x"]-11, 11+73-f["x"]-f["width"])

    def test_C_pair_landscape_equal_rectangles(self):
        p = layout.calculate(request(image("a", 2), image("b", 2)))
        a, b = p["frames"]
        self.assertEqual(p["layout_mode"], "PAIR_LANDSCAPE")
        self.assertAlmostEqual(a["width"], 35)
        self.assertAlmostEqual(a["height"], b["height"])
        self.assertAlmostEqual(b["x"]+b["width"], 73)

    def test_D_pair_portrait_equal_rectangles(self):
        p = layout.calculate(request(image("p1", .6), image("p2", .7)))
        a, b = p["frames"]
        self.assertEqual(p["layout_mode"], "PAIR_PORTRAIT")
        self.assertAlmostEqual(a["height"], b["height"])
        self.assertAlmostEqual(a["width"], b["width"])

    def test_E_pair_mixed_same_height_two_to_one_in_original_order(self):
        for images in [(image("l", 2), image("p", .7)), (image("p", .7), image("l", 2))]:
            p = layout.calculate(request(*images))
            a, b = p["frames"]
            l, portrait = (a, b) if a["orientation"] == "LANDSCAPE" else (b, a)
            self.assertEqual(p["layout_mode"], "PAIR_MIXED")
            self.assertAlmostEqual(l["width"], 2*portrait["width"])
            self.assertAlmostEqual(l["height"], portrait["height"])
            self.assertEqual([f["image_id"] for f in p["frames"]], [i["id"] for i in images])

    def test_F_different_landscape_ratios_crop_to_equal_frames(self):
        p = layout.calculate(request(image("a", 2.2), image("b", 1.6)))
        self.assertTrue(all(f["fit_mode"] == "COVER" for f in p["frames"]))
        self.assertTrue(all(f["crop_or_stretch_policy"]["crop_fraction"] > 0 for f in p["frames"]))
        self.assertAlmostEqual(p["frames"][0]["height"], p["frames"][1]["height"])

    def test_G_transparent_canvas_requires_trim_and_retains_source(self):
        with tempfile.TemporaryDirectory() as temp:
            source, trimmed = Path(temp)/"padded.png", Path(temp)/"trimmed.png"
            im = Image.new("RGBA", (600, 300), (0, 0, 0, 0))
            im.paste((50, 90, 150, 255), (250, 10, 350, 290)); im.save(source)
            before = source.read_bytes()
            with self.assertRaisesRegex(layout.LayoutException, "TRANSPARENT_PADDING"):
                layout.calculate(request({"id": "p", "path": str(source)}))
            result = layout.inspect_image(source, trimmed)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(result["derivative"]["content_bounds_px"], [0, 0, 100, 280])
            p = layout.calculate(request({"id": "p", "path": str(trimmed)}))
            self.assertEqual(p["layout_mode"], "SINGLE_PORTRAIT")
            with self.assertRaisesRegex(layout.LayoutException, "SOURCE_PROTECTION"):
                layout.inspect_image(source, source)

    def test_transparent_interior_is_not_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/"logo.png"
            im = Image.new("RGBA", (30, 30), (10, 20, 30, 255)); im.paste((0, 0, 0, 0), (5, 5, 25, 25)); im.save(p)
            self.assertFalse(layout.inspect_image(p)["alpha_padding"])

    def test_paper_white_is_not_automatically_cropped(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/"scan.png"; Image.new("RGB", (80, 120), "white").save(p)
            self.assertEqual(layout.inspect_image(p)["content_bounds_px"], [0, 0, 80, 120])

    def test_bad_inputs_and_missing_grid_gap(self):
        for change in ({"column_width": -1}, {"column_width": math.nan}, {"gap": 74},
                       {"available_height": 0}, {"layout_mode": "PAIR_PORTRAIT"}):
            with self.subTest(change=change), self.assertRaises(layout.LayoutException):
                layout.calculate(request(image("a", 2), image("b", 2), **change))
        r = request(image("a", 2), image("b", 2)); del r["gap"]
        with self.assertRaises(layout.LayoutException): layout.calculate(r)

    def test_protected_assets_do_not_get_distorted_or_silently_cropped(self):
        for kind in layout.PROTECTED:
            with self.subTest(kind=kind), self.assertRaisesRegex(layout.LayoutException, "PROTECTED_CONTENT"):
                layout.calculate(request(image("l", 2, kind=kind), image("p", .7), allow_landscape_stretch=True))

    def test_mixed_stretch_bounded_and_not_allowed_for_portrait_face_or_text(self):
        r = request(image("l", 2), image("p", 1/1.04), height=70/3*1.04,
                    max_crop_fraction=.01, allow_landscape_stretch=True)
        p = layout.calculate(r)
        self.assertEqual(p["frames"][0]["fit_mode"], "STRETCH")
        self.assertEqual(p["frames"][1]["fit_mode"], "COVER")
        for flag in ("has_faces", "has_text"):
            protected = copy.deepcopy(r); protected["images"][0][flag] = True
            with self.assertRaises(layout.LayoutException): layout.calculate(protected)
        excessive = copy.deepcopy(r); excessive["height"] *= 1.2
        with self.assertRaises(layout.LayoutException): layout.calculate(excessive)

    def test_safe_content_bounds_cannot_be_cropped(self):
        with self.assertRaisesRegex(layout.LayoutException, "KEY_CONTENT_CROP"):
            layout.calculate(request(image("a", 2.2, safe_content_bounds=[0, 0, 1, 1]), image("b", 1.6)))

    def test_height_constraint_returns_exception_not_global_resizing(self):
        with self.assertRaises(layout.LayoutException):
            layout.calculate(request(image("a", .5), available_height=10))
        with self.assertRaisesRegex(layout.LayoutException, "HEIGHT_CONSTRAINT"):
            layout.calculate(request(image("a", 2), height=45, available_height=40))

    def test_common_and_independent_captions_preserved(self):
        for caps in ([{"text": "左图 / 右图", "image_ids": ["a", "b"], "height": 6}],
                     [{"text": "左图", "image_ids": ["a"], "height": 6}, {"text": "右图", "image_ids": ["b"], "height": 6}]):
            p = layout.calculate(request(image("a", 2), image("b", 2), captions=caps, caption_gap=2))
            self.assertTrue(layout.validate_geometry(p, native_fixture(p))["valid"])
            self.assertEqual([c["text"] for c in p["captions"]], [c["text"] for c in caps])
        with self.assertRaisesRegex(layout.LayoutException, "CAPTION_ORDER"):
            layout.calculate(request(image("a", 2), image("b", 2), captions=[{"text": "caption", "image_ids": ["b", "a"], "height": 6}], caption_gap=2))

    def test_validator_reads_graphic_not_only_full_width_frame(self):
        p = layout.calculate(request(image("a", 2))); actual = native_fixture(p)
        actual["items"][0]["graphic"]["width"] *= .7
        result = layout.validate_geometry(p, actual)
        self.assertFalse(result["valid"])
        self.assertIn("VISIBLE_CONTENT_UNDERFILL:a", result["errors"])

    def test_validator_catches_canvas_even_when_frame_and_graphic_match(self):
        p = layout.calculate(request(image("a", 2))); actual = native_fixture(p)
        p["frames"][0]["source"]["content_bounds_px"] = [500, 0, 1000, 1200]
        result = layout.validate_geometry(p, actual)
        self.assertIn("TRANSPARENT_CANVAS:a", result["errors"])
        self.assertIn("VISIBLE_CONTENT_UNDERFILL:a", result["errors"])

    def test_native_wrong_height_order_page_gap_caption_and_overset_rejected(self):
        p = layout.calculate(request(image("a", 2), image("b", 2), captions=[{"text": "caption", "image_ids": ["a", "b"], "height": 6}], caption_gap=2))
        mutations = [lambda a: a["items"][0]["frame"].update(height=25),
                     lambda a: a["items"].reverse(), lambda a: a["items"][1].update(page_id=2),
                     lambda a: a["items"][1]["frame"].update(x=45),
                     lambda a: a["captions"][0].update(overflows=True),
                     lambda a: a["captions"][0]["frame"].update(y=10)]
        for mutate in mutations:
            actual = native_fixture(p); mutate(actual)
            self.assertFalse(layout.validate_geometry(p, actual)["valid"])

    def test_tolerance_instead_of_float_equality(self):
        p = layout.calculate(request(image("a", 2), image("b", 2))); actual = native_fixture(p)
        actual["items"][1]["frame"]["y"] += .49
        self.assertTrue(layout.validate_geometry(p, actual)["valid"])
        actual["items"][1]["frame"]["y"] += .02
        self.assertFalse(layout.validate_geometry(p, actual)["valid"])

    def test_anchored_unit_extra_reserved_space_rejected(self):
        p = layout.calculate(request(image("a", 2))); actual = native_fixture(p)
        actual.update(anchored=True, reserved_height_mm=100)
        self.assertIn("ANCHOR_RESERVED_SPACE", layout.validate_geometry(p, actual)["errors"])

    def test_malformed_native_evidence_cannot_pass(self):
        p = layout.calculate(request(image("a", 2)))
        for bad in ({}, {"items": [{"frame": {}}]}, {"items": []}):
            self.assertFalse(layout.validate_geometry(p, bad)["valid"])

    def test_invalid_contracts_fail_closed(self):
        for r in (None, [], request("not an image"), request(image("a", 2), captions="bad"),
                  request(image("a", 2), defaults={"misspelled_ratio": .7})):
            with self.subTest(request=r), self.assertRaises(layout.LayoutException): layout.calculate(r)
        p = layout.calculate(request(image("a", 2)))
        self.assertFalse(layout.validate_geometry(p, None)["valid"])

    def test_overrides_require_recorded_reason(self):
        r = request(image("a", 2), defaults={"single_landscape_width_ratio": .8})
        with self.assertRaisesRegex(layout.LayoutException, "LAYOUT_EXCEPTION"): layout.calculate(r)
        p = layout.calculate({**r, "override_reason": "Explicit user-requested special plate"})
        self.assertTrue(p["exceptions"])
        self.assertAlmostEqual(p["frames"][0]["width"], 73*.8)

    def test_low_effective_resolution_warns_without_overriding_geometry(self):
        p = layout.calculate(request(image("a", 2))); actual = native_fixture(p)
        actual["items"][0]["effective_ppi"] = [90, 90]
        result = layout.validate_geometry(p, actual)
        self.assertTrue(result["valid"])
        self.assertIn("LOW_EFFECTIVE_PPI:a", result["warnings"])

    def test_native_adapter_jsx_encoding(self):
        for name in ("image_layout_host.jsx", "image_layout_demo.jsx"):
            p = Path(__file__).parents[1]/"scripts"/name
            self.assertTrue(p.read_bytes().startswith(b"\xef\xbb\xbf"), name)

    def test_fractional_widths_never_overflow_or_reorder(self):
        random.seed(7)
        for _ in range(120):
            width = random.uniform(30, 200); gap = random.uniform(.5, width/6)
            p = layout.calculate(request(image("p", .7), image("l", 2), column_width=width, gap=gap, available_height=300))
            self.assertEqual([f["image_id"] for f in p["frames"]], ["p", "l"])
            a, b = p["frames"]
            self.assertGreater(a["height"], 0)
            self.assertAlmostEqual(b["x"]+b["width"], width)


if __name__ == "__main__":
    unittest.main()
