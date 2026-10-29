"""Prepare diagnostic assets/plans or verify/render the native image proof.

Outputs are confined to this skill's ignored .artifacts/image-layout directory.
Synthetic charts are test fixtures, not publication artwork or AI-generated assets.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import uuid

from PIL import Image, ImageDraw
from image_layout import calculate, inspect_image, validate_geometry

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/".artifacts/image-layout"


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf8")


def prepare():
    run = uuid.uuid4().hex[:12]
    folder = OUT/"runs"/run; folder.mkdir(parents=True)
    def chart(name, size, color):
        path = folder/(name+".png")
        image = Image.new("RGB", size, color); draw = ImageDraw.Draw(image)
        for x in range(0, size[0], 100): draw.line((x, 0, x, size[1]), fill="#dddddd", width=3)
        for y in range(0, size[1], 100): draw.line((0, y, size[0], y), fill="#dddddd", width=3)
        cx, cy = size[0]/2, size[1]/2; r = min(size)/4
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill="#eed7ad", outline="#333333", width=8)
        draw.text((size[0]//2-60, size[1]//2), name, fill="black", stroke_width=1)
        image.save(path); return str(path)
    landscape = chart("LANDSCAPE", (1200, 600), "#6d8b9a")
    other = chart("LANDSCAPE-OTHER", (1500, 900), "#947477")
    portrait = chart("PORTRAIT", (600, 900), "#9b9576")
    padded = folder/"PADDED-ORIGINAL.png"
    with Image.open(portrait) as original:
        canvas = Image.new("RGBA", (1500, 900), (0, 0, 0, 0)); canvas.paste(original, (450, 0)); canvas.save(padded)
    trimmed = folder/"PORTRAIT-TRIMMED.png"; inspect_image(padded, trimmed)
    inputs = [
        ("A", "Single landscape", [landscape], "Fills the entire 73mm column; visible content, not just the frame."),
        ("B", "Single portrait", [portrait], "48.667mm width = two thirds of 73mm. Equal side margins."),
        ("C", "Two landscape images", [landscape, landscape], "Equal width and height. 3mm gap comes from this example grid."),
        ("D", "Two portrait images", [portrait, portrait], "Equal frames, shared top and bottom; one-column group."),
        ("E", "Mixed landscape + portrait", [landscape, portrait], "Landscape width is twice portrait width. Same top and bottom."),
        ("F", "Different landscape ratios", [landscape, other], "Proportional cover fit; different crops, identical frame sizes."),
        ("G", "Trimmed transparent margins", [str(trimmed)], "Original padded asset retained. Derived real portrait fills its two-thirds frame."),
    ]
    cases = []
    for index, (ident, title, paths, note) in enumerate(inputs):
        ids = [ident+str(i+1) for i in range(len(paths))]
        request = {"column_width": 73, "available_height": 112, "x": 16 if index % 2 == 0 else 95,
                   "y": 42, "gap": 3, "caption_gap": 2,
                   "images": [{"id": i, "path": path} for i, path in zip(ids, paths)],
                   "captions": [{"text": ident+" / source caption retained", "image_ids": ids, "height": 7}]}
        if ident == "E":
            request["captions"][0].update(text="左图：横屏测试图；右图：竖屏测试图", height=9)
        plan = calculate(request)
        cases.append({"id": ident, "title": title, "note": note, "plan": plan, "expected_valid": True})
    # Controlled native negative case: reproduce a portrait inside a landscape alpha canvas.
    # It intentionally bypasses calculate(), which refuses such an untrimmed asset.
    bad = copy.deepcopy(cases[-1]["plan"]); bad["column"]["x"] = 95
    for frame in bad["frames"]:
        delta = 95-16; frame["x"] += delta; frame["graphic"]["x"] += delta
        frame["source"] = {"id": frame["image_id"], **inspect_image(padded)}
        frame["fit_mode"] = "CONTAIN"
    for cap in bad["captions"]:
        cap["x"] += 95-16
        cap["text"] = cap["display_text"] = "H / intentionally rejected padding"
        cap["display_break_offsets"] = []
    cases.append({"id": "H", "title": "NEGATIVE / padded canvas", "note": "Intentionally wrong. Same outer frame as G, but small visible art. Native validator must reject this case.",
                  "plan": bad, "expected_valid": False})
    almost_square = chart("STRETCH-PORTRAIT", (1000, 1040), "#9b9576")
    stretch_request = {"column_width": 73, "available_height": 112, "x": 16, "y": 42,
                       "gap": 3, "caption_gap": 2, "height": 70/3*1.04,
                       "max_crop_fraction": .01, "allow_landscape_stretch": True,
                       "images": [{"id": "I1", "path": landscape}, {"id": "I2", "path": almost_square}],
                       "captions": [{"text": "I / bounded stretch fixture", "image_ids": ["I1", "I2"], "height": 7}]}
    cases.append({"id": "I", "title": "Mixed / opt-in mild stretch", "note": "Synthetic landscape has a measured 4% axis-ratio change. Portrait stays proportional. Strict assets cannot take this path.",
                  "plan": calculate(stretch_request), "expected_valid": True})
    separate_request = {"column_width": 73, "available_height": 112, "x": 95, "y": 42,
                        "gap": 3, "caption_gap": 2,
                        "images": [{"id": "J1", "path": landscape}, {"id": "J2", "path": other}],
                        "captions": [{"text": "J / left source caption", "image_ids": ["J1"], "height": 7},
                                     {"text": "J / right source caption", "image_ids": ["J2"], "height": 7}]}
    cases.append({"id": "J", "title": "Two independent captions", "note": "Each existing caption retains its own text, frame and image ID. Caption strings are not merged.",
                  "plan": calculate(separate_request), "expected_valid": True})
    request = {"run_id": run, "cases": cases, "pdf": str(folder/"IMAGE_LAYOUT_PROOF.pdf"),
               "indd": str(folder/"IMAGE_LAYOUT_PROOF.indd"), "report": str(folder/"NATIVE_GEOMETRY.json")}
    OUT.mkdir(exist_ok=True)
    write(OUT/"request.json", request)
    # JSON is encoded as a literal, not evaluated from an untrusted file by the host.
    (OUT/"request.jsx").write_text("var IMAGE_LAYOUT_DEMO_REQUEST = "+json.dumps(request, ensure_ascii=True)+";\n", encoding="utf-8-sig")
    print("Prepared run="+run+";9 positive cases + 1 controlled negative;no publication inputs")


def verify():
    from pypdf import PdfReader
    import pypdfium2 as pdfium
    import pdfplumber
    request = json.loads((OUT/"request.json").read_text("utf8"))
    native = json.loads(Path(request["report"]).read_text("utf-8-sig"))
    if native.get("status") != "PASS" or native.get("run_id") != request["run_id"]:
        raise RuntimeError("Native request/result mismatch: "+str(native))
    expected_pages = (len(request["cases"])+1)//2
    if native.get("overset") is not False or native["document_pages"] != expected_pages:
        raise RuntimeError("Unexpected native page/overflow state")
    results = []
    for case, observation in zip(request["cases"], native["cases"]):
        if case["id"] != observation["id"]: raise RuntimeError("Case order changed")
        result = validate_geometry(case["plan"], observation["actual"])
        if any(c.get("left_aligned") is not True for c in observation["actual"]["captions"]):
            raise RuntimeError("Native caption alignment mismatch")
        if any(abs(c["font_size_pt"]-8) > .01 for c in observation["actual"]["captions"]):
            raise RuntimeError("Native caption point-size mismatch (unit conversion)")
        if result["valid"] != case["expected_valid"]: raise RuntimeError(str((case["id"], result)))
        if case["id"] == "H" and not any("TRANSPARENT_CANVAS" in e for e in result["errors"]):
            raise RuntimeError("Native alpha negative was not detected")
        results.append({"case": case["id"], **result, "expected_valid": case["expected_valid"]})
    if len(results) != len(request["cases"]): raise RuntimeError("Missing native cases")
    pdf = Path(request["pdf"]); reader = PdfReader(pdf)
    if len(reader.pages) != expected_pages: raise RuntimeError("PDF page count mismatch")
    for page in reader.pages:
        width, height = float(page.mediabox.width)*25.4/72, float(page.mediabox.height)*25.4/72
        if abs(width-185) > .5 or abs(height-260) > .5: raise RuntimeError("PDF geometry mismatch")
    # Compare actual PDF glyphs in each native caption rectangle. Text extractors
    # may invent CJK punctuation spaces, which are not source/display changes.
    with pdfplumber.open(pdf) as pdf_document:
        for index, (case, observation) in enumerate(zip(request["cases"], native["cases"])):
            page = pdf_document.pages[index//2]
            for cap, measured in zip(case["plan"]["captions"], observation["actual"]["captions"]):
                box = measured["frame"]; pt = 72/25.4
                left, top = box["x"]*pt, box["y"]*pt
                right, bottom = left+box["width"]*pt, top+box["height"]*pt
                chars = [c for c in page.chars
                         if left <= (c["x0"]+c["x1"])/2 <= right and top <= (c["top"]+c["bottom"])/2 <= bottom]
                expected_lines = cap.get("display_text", cap["text"]).split("\n")
                rows = []
                for char in sorted(chars, key=lambda c: (round(c["top"], 1), c["x0"])):
                    if not rows or abs(rows[-1][0]-char["top"]) > .5:
                        rows.append((char["top"], []))
                    rows[-1][1].append(char)
                if len(rows) != len(expected_lines):
                    raise RuntimeError("Caption PDF line count mismatch: "+case["id"])
                for line_index, ((_, glyphs), expected) in enumerate(zip(rows, expected_lines)):
                    actual = "".join(c["text"] for c in sorted(glyphs, key=lambda c: c["x0"]))
                    # InDesign can emit one trailing PDF space for a soft line break.
                    # Accept that exact suffix only on a declared broken line; never
                    # strip source spaces, normalize punctuation, or relax DOM equality.
                    allowed = [expected]
                    if line_index < len(expected_lines)-1:
                        allowed.append(expected+" ")
                    if actual not in allowed:
                        raise RuntimeError("Caption PDF glyph mismatch: "+case["id"])
    folder = pdf.parent; document = pdfium.PdfDocument(str(pdf)); thumbs = []
    try:
        for index in range(len(document)):
            page = document[index]; bitmap = page.render(scale=160/72)
            try:
                image = bitmap.to_pil().convert("RGB"); image.save(folder/f"page-{index+1}.png")
                image.thumbnail((500, 720)); thumbs.append(image)
            finally: bitmap.close(); page.close()
    finally: document.close()
    contact = Image.new("RGB", (1020, ((expected_pages+1)//2)*740), "#eeeeee"); draw = ImageDraw.Draw(contact)
    for index, image in enumerate(thumbs):
        x, y = index % 2*510, index//2*740
        contact.paste(image, (x, y+18)); draw.text((x+8, y+2), str(index+1), fill="black")
    contact.save(folder/"IMAGE_LAYOUT_CONTACT.png")
    result = {"status": "PASS", "run_id": request["run_id"], "native_version": native["native_version"],
              "pdf": str(pdf), "pages": expected_pages, "overset": False, "geometry_cases": results,
              "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(), "visual_review": "PENDING"}
    write(folder/"VALIDATION.json", result)
    print(f"PASS native geometry;{len(results)-1} accepted + alpha negative rejected;{expected_pages} PDF pages rendered;"+str(folder))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("phase", choices=["prepare", "verify"])
    args = parser.parse_args(); {"prepare": prepare, "verify": verify}[args.phase]()
