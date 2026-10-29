"""Column image geometry in mm; plan frames, inspect alpha, validate native objects.

Python 3.10+. Pillow is needed only for real raster inspection/transparent trimming.
No publication is changed by this module. Exceptions are explicit, never silent fits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

MODES = {"SINGLE_LANDSCAPE", "SINGLE_PORTRAIT", "PAIR_LANDSCAPE", "PAIR_PORTRAIT", "PAIR_MIXED"}
DEFAULTS = {
    "single_landscape_width_ratio": 1.0,
    "single_portrait_width_ratio": 0.6666667,
    "pair_same_orientation_equal_width": True,
    "pair_same_orientation_equal_height": True,
    "pair_mixed_landscape_to_portrait_width_ratio": 2.0,
    "pair_top_alignment": True,
    "pair_bottom_alignment": True,
}
PROTECTED = {"logo", "emblem", "qr", "text", "archive", "face"}


class LayoutException(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def caption_display(text: str, break_offsets: list[int] | None = None) -> tuple[str, list[int]]:
    """Insert display-only breaks before left/right labels; never replace source chars."""
    if break_offsets is None:
        matches = list(re.finditer(r"[（(【\[]?[左右]图", text))
        left = [m for m in matches if "左图" in m.group()]
        right = [m for m in matches if "右图" in m.group()]
        if not left or not right:
            return text, []
        if len(left) != 1 or len(right) != 1:
            raise LayoutException("CAPTION_LABELS_AMBIGUOUS", "supply explicit display_break_offsets")
        break_offsets = [m.start() for m in matches if m.start() > 0 and text[m.start()-1] not in "\n\r\u2028"]
    if (not isinstance(break_offsets, list) or any(isinstance(p, bool) or not isinstance(p, int)
            or not 0 < p < len(text) for p in break_offsets) or break_offsets != sorted(set(break_offsets))):
        raise LayoutException("CAPTION_BREAK_OFFSETS", "expected ordered unique source-character offsets")
    displayed = text
    for offset in reversed(break_offsets):
        displayed = displayed[:offset]+"\n"+displayed[offset:]
    return displayed, list(break_offsets)


def restore_caption(displayed: str, offsets: list[int]) -> str:
    for index, offset in reversed(list(enumerate(offsets))):
        actual = offset+index
        if displayed[actual:actual+1] != "\n":
            raise LayoutException("CAPTION_RECONSTRUCTION", "authorized display break missing")
        displayed = displayed[:actual]+displayed[actual+1:]
    return displayed


def number(value, name: str, *, positive: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise LayoutException("INVALID_INPUT", name + " must be finite")
    if (positive and value <= 0) or (not positive and value < 0):
        raise LayoutException("INVALID_INPUT", name + " has an invalid sign")
    return float(value)


def inspect_image(path: str | Path, trim_output: str | Path | None = None) -> dict:
    from PIL import Image
    path = Path(path).resolve()
    original = path.read_bytes()
    with Image.open(path) as image:
        width, height = image.size
        rgba = image.convert("RGBA")
        bounds = rgba.getchannel("A").getbbox()  # Keep every nonzero-alpha pixel, including edge antialiasing.
        if not bounds:
            raise LayoutException("EMPTY_IMAGE", str(path))
        result = {"path": str(path), "width_px": width, "height_px": height,
                  "content_bounds_px": list(bounds), "sha256": hashlib.sha256(original).hexdigest(),
                  "alpha_padding": bounds != (0, 0, width, height)}
        if trim_output is not None:
            target = Path(trim_output).resolve()
            if target == path or target.exists():
                raise LayoutException("SOURCE_PROTECTION", "trim target must be new and different from source")
            target.parent.mkdir(parents=True, exist_ok=True)
            rgba.crop(bounds).save(target, "PNG")
            result["derivative"] = inspect_image(target)
    if path.read_bytes() != original:
        raise LayoutException("SOURCE_PROTECTION", "source bytes changed")
    return result


def image_info(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise LayoutException("INVALID_INPUT", "each image must be an object")
    image = dict(raw)
    if image.get("path"):
        image.update(inspect_image(image["path"]))  # Actual pixels override claimed dimensions/alpha bounds.
    width = number(image.get("width_px"), "width_px")
    height = number(image.get("height_px"), "height_px")
    bounds = image.get("content_bounds_px", [0, 0, width, height])
    if len(bounds) != 4 or not all(isinstance(n, (int, float)) and math.isfinite(n) for n in bounds):
        raise LayoutException("INVALID_INPUT", "invalid content bounds")
    left, top, right, bottom = bounds
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise LayoutException("INVALID_INPUT", "content bounds outside source")
    image.update(width_px=width, height_px=height, content_bounds_px=list(bounds),
                 aspect_ratio=(right-left)/(bottom-top))
    image["orientation"] = "LANDSCAPE" if image["aspect_ratio"] >= 1 else "PORTRAIT"
    if bounds != [0, 0, width, height] and tuple(bounds) != (0, 0, width, height):
        raise LayoutException("TRANSPARENT_PADDING", f"{image.get('id')}: trim outer alpha into a derivative before placement")
    return image


def fitting(image: dict, frame: dict, request: dict) -> dict:
    iw, ih = image["width_px"], image["height_px"]
    fw, fh = frame["width"], frame["height"]
    contain, cover = min(fw/iw, fh/ih), max(fw/iw, fh/ih)
    lost = 1 - (fw * fh) / ((cover*iw)*(cover*ih))
    protected = image.get("kind") in PROTECTED or image.get("strict_proportion", False)
    allow_crop = image.get("allow_crop", not protected)
    crop_limit = number(request.get("max_crop_fraction", 0.30), "max_crop_fraction", positive=False)
    if crop_limit > 1:
        raise LayoutException("INVALID_INPUT", "max_crop_fraction must be <= 1")
    fit = "COVER"
    review = False
    if lost > 1e-9 and not allow_crop:
        raise LayoutException("PROTECTED_CONTENT", f"{image['id']}: requested frame requires unauthorized crop")
    if lost > crop_limit + 1e-9:
        # Stretch is bounded and only an alternative for the landscape in a mixed pair.
        stretch = max((fw/iw)/(fh/ih), (fh/ih)/(fw/iw))
        limit = number(request.get("max_stretch_ratio", 1.08), "max_stretch_ratio")
        if limit < 1:
            raise LayoutException("INVALID_INPUT", "max_stretch_ratio must be >= 1")
        if (request["layout_mode"] == "PAIR_MIXED" and image["orientation"] == "LANDSCAPE"
                and request.get("allow_landscape_stretch", False) and not protected
                and not image.get("has_faces") and not image.get("has_text") and stretch <= limit):
            fit = "STRETCH"
        else:
            raise LayoutException("EXCESSIVE_CROP", f"{image['id']}: crop {lost:.1%}; change height or record a layout exception")
    if fit == "STRETCH":
        gw, gh = fw, fh
    else:
        gw, gh = iw*cover, ih*cover
        review = lost > 1e-9
    gx, gy = frame["x"]+(fw-gw)/2, frame["y"]+(fh-gh)/2
    visible_source = [(frame["x"]-gx)/gw, (frame["y"]-gy)/gh,
                      (frame["x"]+fw-gx)/gw, (frame["y"]+fh-gy)/gh]
    safe = image.get("safe_content_bounds")  # Normalized source region that must remain visible.
    if safe:
        if len(safe) != 4 or not (0 <= safe[0] < safe[2] <= 1 and 0 <= safe[1] < safe[3] <= 1):
            raise LayoutException("INVALID_INPUT", "invalid safe_content_bounds")
        if any((safe[i] < visible_source[i]-1e-9 if i < 2 else safe[i] > visible_source[i]+1e-9) for i in range(4)):
            raise LayoutException("KEY_CONTENT_CROP", image["id"] + ": protected region would be cropped")
        review = False
    return {"fit_mode": fit, "crop_or_stretch_policy": {
        "crop_fraction": 0 if fit == "STRETCH" else max(0, lost),
        "stretch_limit": request.get("max_stretch_ratio", 1.08) if fit == "STRETCH" else 1,
        "crop_review_required": review, "protected_content": protected},
        "graphic": {"x": gx, "y": gy, "width": gw, "height": gh}}


def calculate(request: dict) -> dict:
    """All x/y/width/height inputs and outputs are mm in page-local coordinates."""
    if not isinstance(request, dict):
        raise LayoutException("INVALID_INPUT", "request must be an object")
    width = number(request.get("column_width"), "column_width")
    available = number(request.get("available_height"), "available_height")
    x = number(request.get("x", 0), "x", positive=False)
    y = number(request.get("y", 0), "y", positive=False)
    raw = request.get("images", [])
    if not isinstance(raw, list) or len(raw) not in (1, 2):
        raise LayoutException("IMAGE_COUNT", "only one or two images per unit")
    images = [image_info(image) for image in raw]
    ids = [image.get("id") for image in images]
    if not all(isinstance(i, str) and i for i in ids) or len(set(ids)) != len(ids):
        raise LayoutException("IMAGE_ORDER", "image IDs must be nonempty and unique")
    orientations = [i["orientation"] for i in images]
    inferred = ("SINGLE_" + orientations[0]) if len(images) == 1 else (
        "PAIR_" + orientations[0] if orientations[0] == orientations[1] else "PAIR_MIXED")
    mode = request.get("layout_mode", inferred)
    if mode not in MODES or mode != inferred:
        raise LayoutException("LAYOUT_MODE", "mode/count/orientation mismatch: expected " + inferred)
    settings = request.get("defaults", {})
    if not isinstance(settings, dict) or any(k not in DEFAULTS for k in settings):
        raise LayoutException("INVALID_INPUT", "unknown/nonobject defaults")
    options = {**DEFAULTS, **settings}
    overrides = {key: value for key, value in options.items() if key in DEFAULTS and value != DEFAULTS[key]}
    if overrides and not request.get("override_reason"):
        raise LayoutException("LAYOUT_EXCEPTION", "custom defaults require an explicit override_reason")
    # These invariants are structural. Special treatments belong to named exceptions, not disabled assertions.
    for key in ("pair_same_orientation_equal_width", "pair_same_orientation_equal_height", "pair_top_alignment", "pair_bottom_alignment"):
        if options[key] is not True:
            raise LayoutException("LAYOUT_EXCEPTION", "cannot disable " + key)
    gap = number(request.get("gap"), "grid gap", positive=False) if len(images) == 2 else 0
    if gap >= width:
        raise LayoutException("INVALID_INPUT", "gap must be smaller than column")
    captions = request.get("captions", [])
    if not isinstance(captions, list) or any(not isinstance(c, dict) for c in captions):
        raise LayoutException("CAPTION_CONTRACT", "captions must be a list of objects")
    if len(captions) > 2:
        raise LayoutException("CAPTION_CONTRACT", "one common caption or up to two independent captions")
    cap_gap = number(request.get("caption_gap"), "caption_gap", positive=False) if captions else 0
    reserve = max([number(c.get("height"), "caption height") for c in captions] or [0])
    max_height = available - reserve - cap_gap
    if max_height <= 0:
        raise LayoutException("HEIGHT_CONSTRAINT", "no image room after caption reservation")
    if len(images) == 1:
        ratio = number(options["single_" + orientations[0].lower() + "_width_ratio"], "single width ratio")
        if ratio > 1:
            raise LayoutException("FRAME_OVERFLOW", "single width ratio exceeds column")
        widths = [width*ratio]
    elif mode == "PAIR_MIXED":
        ratio = number(options["pair_mixed_landscape_to_portrait_width_ratio"], "mixed width ratio")
        portrait = (width-gap)/(ratio+1)
        widths = [portrait*ratio if o == "LANDSCAPE" else portrait for o in orientations]
    else:
        widths = [(width-gap)/2]*2
    natural = [w/i["aspect_ratio"] for w, i in zip(widths, images)]
    # Geometric mean minimizes the largest multiplicative aspect mismatch for two frames.
    target = natural[0] if len(images) == 1 else math.sqrt(natural[0]*natural[1])
    height = number(request.get("height", min(target, max_height)), "height")
    if height > max_height + 1e-9:
        raise LayoutException("HEIGHT_CONSTRAINT", "requested image/caption unit exceeds available height")
    frames = []
    next_x = x+(width-widths[0])/2 if len(images) == 1 else x
    for image, fw in zip(images, widths):
        frame = {"image_id": image["id"], "x": next_x, "y": y, "width": fw, "height": height,
                 "orientation": image["orientation"], "image_count": len(images), "layout_mode": mode,
                 "source": image}
        frame.update(fitting(image, frame, {**request, "layout_mode": mode}))
        frames.append(frame)
        next_x += fw+gap
    cap_frames = []
    referenced = []
    for caption in captions:
        ref = caption.get("image_ids", [])
        if not isinstance(caption.get("text"), str) or not ref or any(i not in ids for i in ref):
            raise LayoutException("CAPTION_CONTRACT", "caption must retain source text and image IDs")
        if ref != [i for i in ids if i in ref] or any(i in referenced for i in ref):
            raise LayoutException("CAPTION_ORDER", "caption order/association mismatch")
        referenced += ref
        group = [f for f in frames if f["image_id"] in ref]
        left = group[0]["x"]
        right = group[-1]["x"]+group[-1]["width"]
        display, offsets = caption_display(caption["text"], caption.get("display_break_offsets"))
        cap_frames.append({"x": left, "y": y+height+cap_gap, "width": right-left,
                           "height": caption["height"], "text": caption["text"], "image_ids": ref,
                           "display_text": display, "display_break_offsets": offsets})
    return {"status": "READY", "units": "mm", "layout_mode": mode, "image_count": len(images),
            "column": {"x": x, "y": y, "width": width, "height": available}, "gap": gap,
            "defaults": options, "frames": frames, "captions": cap_frames,
            "height": height+reserve+cap_gap, "visual_review": "REQUIRED",
            "min_effective_ppi": number(request.get("min_effective_ppi", 150), "min_effective_ppi"),
            "exceptions": [{"reason": request["override_reason"], "overrides": overrides}] if overrides else []}


def overlap(a: dict, b: dict, tolerance: float) -> bool:
    return (min(a["x"]+a["width"], b["x"]+b["width"])-max(a["x"], b["x"]) > tolerance
            and min(a["y"]+a["height"], b["y"]+b["height"])-max(a["y"], b["y"]) > tolerance)


def validate_geometry(plan: dict, actual: dict, tolerance: float = 0.5) -> dict:
    """Read observed native frame AND graphic geometry, never just the planned boxes.

    The native adapter records placed link paths; source alpha is re-inspected here.
    This is geometry acceptance, not a substitute for PDF visual/crop review.
    """
    tolerance = number(tolerance, "tolerance")
    if not isinstance(plan, dict) or plan.get("status") != "READY" or not isinstance(actual, dict):
        return {"valid": False, "errors": ["INVALID_PLAN_OR_NATIVE_REPORT"]}
    errors, warnings = [], []
    def require(value, code):
        if not value:
            errors.append(code)
    require(actual.get("origin") == "InDesign_DOM" and actual.get("units") == "mm", "NATIVE_EVIDENCE_REQUIRED")
    if not actual.get("items") or len(actual["items"]) != len(plan["frames"]):
        return {"valid": False, "errors": errors+["IMAGE_COUNT"]}
    for observed in actual["items"]:
        if any(not isinstance(observed.get(key), dict) or any(not isinstance(observed[key].get(k), (int, float))
               or not math.isfinite(observed[key][k]) for k in ("x", "y", "width", "height"))
               for key in ("frame", "graphic")):
            return {"valid": False, "errors": errors+["MALFORMED_NATIVE_GEOMETRY"]}
    require([a.get("image_id") for a in actual["items"]] == [f["image_id"] for f in plan["frames"]], "IMAGE_ORDER")
    visible = []
    column = plan["column"]
    for expected, observed in zip(plan["frames"], actual["items"]):
        ident = expected["image_id"]
        try:
            box, graphic = observed["frame"], observed["graphic"]
            for b in (box, graphic):
                for key in ("width", "height"):
                    number(b[key], key)
            require(observed.get("page_id") is not None and not observed.get("link_missing"), "PAGE_OR_LINK:"+ident)
            ppi = observed.get("effective_ppi", [])
            if ppi and min(ppi) < plan.get("min_effective_ppi", 150):
                warnings.append("LOW_EFFECTIVE_PPI:"+ident)
            require(abs(observed.get("rotation", 0)) < 0.001 and abs(observed.get("shear", 0)) < 0.001, "NON_AXIS_ALIGNED:"+ident)
            for key in ("x", "y", "width", "height"):
                require(abs(box[key]-expected[key]) <= tolerance, "FRAME_GEOMETRY:"+ident+":"+key)
                require(abs(graphic[key]-expected["graphic"][key]) <= tolerance, "GRAPHIC_GEOMETRY:"+ident+":"+key)
            require(box["x"] >= column["x"]-tolerance and box["x"]+box["width"] <= column["x"]+column["width"]+tolerance, "FRAME_OVERFLOW:"+ident)
            require(box["y"] >= column["y"]-tolerance and box["y"]+box["height"] <= column["y"]+column["height"]+tolerance, "FRAME_OVERFLOW:"+ident)
            source = expected["source"]
            if source.get("path"):
                require(Path(observed.get("source_path", "")).resolve() == Path(source["path"]).resolve(), "SOURCE_LINK:"+ident)
                info = inspect_image(observed["source_path"])
                require(info["sha256"] == source["sha256"], "SOURCE_CHANGED:"+ident)
            else:
                info = source  # Used by pure unit-test fixtures; real placement uses linked assets.
            iw, ih = info["width_px"], info["height_px"]
            l, t, r, b = info.get("content_bounds_px", [0, 0, iw, ih])
            content = {"x": graphic["x"]+graphic["width"]*l/iw, "y": graphic["y"]+graphic["height"]*t/ih,
                       "width": graphic["width"]*(r-l)/iw, "height": graphic["height"]*(b-t)/ih}
            left, top = max(content["x"], box["x"]), max(content["y"], box["y"])
            right = min(content["x"]+content["width"], box["x"]+box["width"])
            bottom = min(content["y"]+content["height"], box["y"]+box["height"])
            visible.append({"x": left, "y": top, "width": max(0, right-left), "height": max(0, bottom-top)})
            require(abs(right-left-box["width"]) <= tolerance and abs(bottom-top-box["height"]) <= tolerance,
                    "VISIBLE_CONTENT_UNDERFILL:"+ident)
            if (l, t, r, b) != (0, 0, iw, ih):
                require(False, "TRANSPARENT_CANVAS:"+ident)
            distorted = max((graphic["width"]/iw)/(graphic["height"]/ih), (graphic["height"]/ih)/(graphic["width"]/iw))
            limit = expected["crop_or_stretch_policy"]["stretch_limit"]
            require(distorted <= limit+0.001, "DISTORTION:"+ident)
        except (KeyError, ValueError, OSError, TypeError) as error:
            errors.append("INVALID_NATIVE_RECORD:"+ident+":"+str(error))
    items = actual["items"]
    if len(items) == 2:
        a, b = [i["frame"] for i in items]
        require(abs(a["y"]-b["y"]) <= tolerance, "PAIR_TOP")
        require(abs(a["y"]+a["height"]-b["y"]-b["height"]) <= tolerance, "PAIR_BOTTOM")
        require(abs(a["height"]-b["height"]) <= tolerance, "PAIR_HEIGHT")
        require(abs(b["x"]-a["x"]-a["width"]-plan["gap"]) <= tolerance, "PAIR_GAP")
        if plan["layout_mode"] == "PAIR_MIXED":
            l, p = (a, b) if plan["frames"][0]["orientation"] == "LANDSCAPE" else (b, a)
            require(abs(l["width"]-p["width"]*plan["defaults"]["pair_mixed_landscape_to_portrait_width_ratio"]) <= tolerance, "PAIR_MIXED_RATIO")
        else:
            require(abs(a["width"]-b["width"]) <= tolerance, "PAIR_WIDTH")
    actual_caps = actual.get("captions", [])
    require(len(actual_caps) == len(plan["captions"]), "CAPTION_COUNT")
    for expected, observed in zip(plan["captions"], actual_caps):
        if not isinstance(observed.get("frame"), dict) or any(not isinstance(observed["frame"].get(k), (int, float))
               or not math.isfinite(observed["frame"][k]) for k in ("x", "y", "width", "height")):
            errors.append("MALFORMED_CAPTION_GEOMETRY")
            continue
        require(observed.get("text") == expected.get("display_text", expected["text"])
                and observed.get("image_ids") == expected["image_ids"], "CAPTION_TEXT_OR_ORDER")
        try:
            require(restore_caption(observed.get("text", ""), expected.get("display_break_offsets", [])) == expected["text"],
                    "CAPTION_SOURCE_RECONSTRUCTION")
        except LayoutException:
            errors.append("CAPTION_SOURCE_RECONSTRUCTION")
        require(not observed.get("overflows", True), "CAPTION_OVERSET")
        require(observed.get("left_aligned", True) is True, "CAPTION_ALIGNMENT")
        require(observed.get("page_id") == items[0].get("page_id"), "CAPTION_PAGE")
        for key in ("x", "y", "width", "height"):
            require(abs(observed["frame"][key]-expected[key]) <= tolerance, "CAPTION_GEOMETRY")
        for image in items:
            require(not overlap(observed["frame"], image["frame"], 0.01), "CAPTION_OVERLAP")
    require(len({i.get("page_id") for i in items}) == 1, "PAIR_PAGE")
    if actual.get("anchored"):
        reserved = actual.get("reserved_height_mm")
        require(isinstance(reserved, (int, float)) and abs(reserved-plan["height"]) <= tolerance,
                "ANCHOR_RESERVED_SPACE")
    return {"valid": not errors, "errors": errors, "warnings": warnings, "visible_bounds": visible,
            "tolerance_mm": tolerance, "visual_review": "REQUIRED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("plan"); p.add_argument("request", type=Path); p.add_argument("--out", type=Path)
    p = sub.add_parser("inspect"); p.add_argument("image", type=Path); p.add_argument("--trim-output", type=Path)
    p = sub.add_parser("validate"); p.add_argument("plan", type=Path); p.add_argument("native", type=Path); p.add_argument("--tolerance", type=float, default=0.5)
    args = parser.parse_args()
    read = lambda p: json.loads(p.read_text("utf-8-sig"))
    try:
        if args.action == "plan":
            result = calculate(read(args.request))
            if args.out:
                args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
        elif args.action == "inspect":
            result = inspect_image(args.image, args.trim_output)
        else:
            result = validate_geometry(read(args.plan), read(args.native), args.tolerance)
    except (LayoutException, OSError, KeyError, TypeError) as error:
        result = {"status": "EXCEPTION", "code": getattr(error, "code", "INVALID_INPUT"), "reason": str(error)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("status") == "EXCEPTION" or result.get("valid") is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
