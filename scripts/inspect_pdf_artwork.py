#!/usr/bin/env python3
"""Read-only validation for print PDF page and trim/bleed geometry."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from pypdf import PdfReader


MM_PER_PT = 25.4 / 72


def box_mm(box: Any) -> list[float]:
    return [round(float(value) * MM_PER_PT, 6) for value in box]


def size_mm(box: Any) -> tuple[float, float]:
    return float(box.width) * MM_PER_PT, float(box.height) * MM_PER_PT


def close(actual: float, expected: float, tolerance: float) -> bool:
    return abs(actual - expected) <= tolerance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--trim-mm", type=float, nargs=2, metavar=("WIDTH", "HEIGHT"), required=True)
    parser.add_argument("--bleed-mm", type=float, default=0)
    parser.add_argument("--rotation", type=int, default=0)
    parser.add_argument("--sha256")
    parser.add_argument("--tolerance-mm", type=float, default=0.001)
    args = parser.parse_args()

    payload = args.pdf.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    reader = PdfReader(args.pdf)
    errors: list[str] = []

    if reader.is_encrypted:
        errors.append("PDF is encrypted")
        result = {
            "path": str(args.pdf.resolve()),
            "sha256": digest,
            "encrypted": True,
            "page_count": None,
            "pages": [],
            "valid": False,
            "errors": errors,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    if len(reader.pages) != args.pages:
        errors.append(f"page count {len(reader.pages)} != {args.pages}")
    if args.sha256 and digest.lower() != args.sha256.lower():
        errors.append("SHA-256 mismatch")

    expected_media = (
        args.trim_mm[0] + 2 * args.bleed_mm,
        args.trim_mm[1] + 2 * args.bleed_mm,
    )
    pages: list[dict[str, Any]] = []
    for index, page in enumerate(reader.pages):
        boxes = {
            "media": box_mm(page.mediabox),
            "crop": box_mm(page.cropbox),
            "trim": box_mm(page.trimbox),
            "bleed": box_mm(page.bleedbox),
            "art": box_mm(page.artbox),
        }
        media_size = size_mm(page.mediabox)
        crop_size = size_mm(page.cropbox)
        bleed_size = size_mm(page.bleedbox)
        trim_size = size_mm(page.trimbox)
        if not all(close(a, e, args.tolerance_mm) for a, e in zip(media_size, expected_media)):
            errors.append(f"page {index + 1} MediaBox size {media_size} != {expected_media}")
        if not all(close(a, e, args.tolerance_mm) for a, e in zip(trim_size, args.trim_mm)):
            errors.append(f"page {index + 1} TrimBox size {trim_size} != {tuple(args.trim_mm)}")
        if not all(close(a, e, args.tolerance_mm) for a, e in zip(crop_size, expected_media)):
            errors.append(f"page {index + 1} CropBox size {crop_size} != {expected_media}")
        if not all(close(a, e, args.tolerance_mm) for a, e in zip(bleed_size, expected_media)):
            errors.append(f"page {index + 1} BleedBox size {bleed_size} != {expected_media}")
        if page.rotation != args.rotation:
            errors.append(f"page {index + 1} rotation {page.rotation} != {args.rotation}")
        if args.bleed_mm:
            expected_trim = (
                args.bleed_mm,
                args.bleed_mm,
                args.bleed_mm + args.trim_mm[0],
                args.bleed_mm + args.trim_mm[1],
            )
            actual_trim = tuple(float(value) * MM_PER_PT for value in page.trimbox)
            if not all(close(a, e, args.tolerance_mm) for a, e in zip(actual_trim, expected_trim)):
                errors.append(f"page {index + 1} TrimBox offsets {actual_trim} != {expected_trim}")
        pages.append({"index": index + 1, "rotation": page.rotation, "boxes_mm": boxes})

    result = {
        "path": str(args.pdf.resolve()),
        "sha256": digest,
        "encrypted": reader.is_encrypted,
        "page_count": len(reader.pages),
        "pages": pages,
        "valid": not errors,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
