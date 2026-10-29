# Column image geometry contract

Default for **new, ordinary body-image units**. Explicit user instructions win. Approved/frozen pages and named project exceptions remain intact; adopting this Skill does not authorize rebuilding them. A single column means the actual current grid column, not the whole two-column live area.

## Five modes (all measurements in mm)

Let `W` be usable column width and `G` be the publication grid's image gap. `G` is required for pairs; there is no global mm default. Page-local `x,y` identify the available region. Captions and caption gap are reserved before solving image height.

| Mode | Frame widths | Height and alignment |
| --- | --- | --- |
| `SINGLE_LANDSCAPE` | `W` | Natural height `W / source_aspect`; left/right coincide with column edges. Check **visible content** spans the width. |
| `SINGLE_PORTRAIT` | `W × 0.6666667` (2/3 to numerical tolerance) | Center horizontally; equal side margins; natural height from actual content aspect. |
| `PAIR_LANDSCAPE` | each `(W-G)/2` | One common height, equal top/bottom, gap `G`. |
| `PAIR_PORTRAIT` | each `(W-G)/2` | One common height, equal top/bottom, gap `G`. |
| `PAIR_MIXED` | landscape `2(W-G)/3`; portrait `(W-G)/3` | One common height, equal top/bottom. Preserve original order even if the portrait comes first. |

For pairs, the solver's natural common height is the geometric mean of the two natural frame heights; it minimizes the larger multiplicative aspect mismatch. A supplied positive `height` overrides this choice. Height must fit the available region including captions. Proportional cover fit is preferred; review actual crop against important people, lettering and archival information. If the crop is unsafe, exceeds the configured limit, or a protected asset cannot fit, the solver raises a structured exception. Change the local height, insertion position or named layout treatment; do not silently shrink widths or all body type to make the geometry pass.

Square images count as landscape by default. An explicit incompatible mode/count/orientation is rejected. Orientation is determined from real nontransparent content, not an alpha-padded landscape canvas. A padded asset must first be replaced by an authorized, traceable transparent-margin derivative. Interior transparent holes and opaque white paper are preserved.

Defaults exported by `scripts/image_layout.py`:

```json
{
  "single_landscape_width_ratio": 1.0,
  "single_portrait_width_ratio": 0.6666667,
  "pair_same_orientation_equal_width": true,
  "pair_same_orientation_equal_height": true,
  "pair_mixed_landscape_to_portrait_width_ratio": 2.0,
  "pair_top_alignment": true,
  "pair_bottom_alignment": true
}
```

Ratios can be parameterized through `defaults`, with a required `override_reason` for changes. Structural alignment invariants cannot be disabled to hide a defect. For an incompatible special layout, record a separate named exception (asset/source ID, requested rule, measured deviation, reason and approval status). Do not describe an exception as a default PASS.

## Executable interface

The shared calculator is Python, so modules do not repeat geometry arithmetic in JSX. It uses only the standard library for numerical planning; Pillow is required to inspect real raster assets/alpha. Calculate during the existing project's preparation stage, then pass the JSON plan to the renderer. Do not add another process per picture.

```python
from image_layout import calculate, inspect_image, validate_geometry

plan = calculate({
    "column_width": 73, "available_height": 100,
    "x": 16, "y": 42, "gap": 3, "caption_gap": 2,
    "images": [
        {"id": "source-image-1", "path": "activity.png"},
        {"id": "source-image-2", "path": "poster.png"}
    ],
    "captions": [
        {"text": "Verbatim existing common caption", "image_ids": ["source-image-1", "source-image-2"], "height": 7}
    ]
})
```

The mm values above are sample grid inputs, **not defaults**. `captions` may be empty, one common source caption, or independent source captions. Independent caption widths follow their associated frames; do not invent/merge captions or reverse left/right references. Caption height is a measured style reservation, not permission to clip/shorten text; native overset must still be checked.

Each output frame includes `x,y,width,height,image_count,layout_mode,fit_mode,crop_or_stretch_policy`, source identity/hash/alpha bounds, and the expected placed-graphic envelope. The plan also includes the column, captions and required visual-review state. Preserve stable event/year/paragraph/image anchors outside this geometry utility.

Sources without paths can provide `width_px,height_px` for planning/tests, but this is not pixel inspection or native acceptance. Real placement/validation requires linked paths; metadata is re-read from the actual linked files, not accepted from claimed dimensions.

```powershell
python scripts/image_layout.py inspect original.png --trim-output trimmed-new.png
python scripts/image_layout.py plan request.json --out plan.json
python scripts/image_layout.py validate plan.json native.json --tolerance 0.5
```

`inspect` never modifies the original. `--trim-output` must be new and different; only outer zero-alpha margins are removed. Keep source hash and derivative relationship. Completely transparent images fail. Opaque white margins/scans require human inspection; do not infer that white pixels are disposable.

## Crop, stretch and quality

- Ordinary photos/illustrations allow proportional cover cropping by default, subject to crop review. `max_crop_fraction=0.30` is a configurable conservative review guard, not a license to remove up to 30% of critical content. `safe_content_bounds=[left,top,right,bottom]` gives a normalized region that must survive the crop; otherwise a nonzero crop retains `crop_review_required=true` until the actual PDF has been inspected.
- `kind` in `logo,emblem,qr,text,archive,face` or `strict_proportion=true` prevents default cropping and all nonuniform stretching. Explicit `allow_crop=true` can authorize a safe proportional crop for a particular protected asset; it does not authorize distortion. Record any protected-content exception.
- Only the landscape member of `PAIR_MIXED` may opt into `allow_landscape_stretch=true`. It is an alternative after safe cover fit exceeds the configured crop limit, capped by `max_stretch_ratio` (default 1.08 between axis scales). The portrait, strict assets, or images flagged `has_faces/has_text` do not take this path. The cap is a technical bound, not visual acceptance: inspect faces/lettering and reject visible deformation. Do not modify source bytes.
- Read effective PPI from native graphics (`min_effective_ppi=150`, configurable advisory threshold, never a geometry-fatal assertion), preserve source originals, flag low resolution, preserve text/source sequence and semantic anchors. Low resolution or inability to crop safely can warrant a documented layout exception rather than upscaling or distorted evidence.

## Native verification and whitespace

Include `scripts/image_layout_host.jsx` for the reusable placer/snapshot adapter, or integrate its narrow snapshot contract into an existing renderer. Set page-local and script measurement units to millimetres explicitly, restore caller settings afterwards, and use explicit `pt` strings for text sizes/leading so caption typography does not accidentally inherit millimetres. `snapshot()` resolves actual rectangles, graphics and links after recomposition; it does not copy proposed dimensions into the native report. It records actual frame/graphic bounds, source path, page, rotation/shear, link status, PPI, caption text and caption overset.

`validate_geometry()` reads that native report, re-inspects actual linked pixels and clips their content envelope to the frame. It checks planned geometry with a default **0.5mm tolerance**, column containment, visible underfill, alpha padding, pair top/bottom/height/width/gap or mixed 2:1 ratio, page/order, caption text/association/overlap and distortion. Graphic extents outside a frame are allowed only as clipped cover fitting, not overflowing page frames.

The adapter is deliberately for axis-aligned raster frames. Rotated/sheared or vector-only assets, irregular wrap and nonstandard treatments require explicit extensions/exception evidence, not fabricated alpha bounds. For anchored units, production integration must set `anchored=true` and measure `reserved_height_mm` from the actual paragraph/anchor layout; the standalone nonanchored proof does not claim to test anchored flow. Excess reserved height fails rather than passing on rectangle width alone.

Visible alpha bounds catch transparent padding, but not every perceptual blank region. Inspect opaque paper margins, subjects, inter-paragraph whitespace and neighboring pages in the exported PDF. Geometry PASS is not visual PASS. No blanket page-fill percentage is imposed; deliberate whitespace, source associations, protected content and approved pages take priority over filling every region.

## Tests and independent host proof

```powershell
python -m unittest discover -s tests -v
powershell -File scripts/run_image_layout_demo.ps1 -Python python
```

Python runtime needs Pillow for raster fixtures; the optional host proof also uses pypdf and pypdfium2. Reuse available runtimes; do not install another stack merely for this Skill.

The host proof creates **only a new diagnostic document**: A–E exercise the five modes, F covers unequal landscape ratios, G uses a trimmed alpha derivative, H is an intentionally bad transparent-canvas placement that the native validator must reject. I additionally exercises bounded landscape stretching and J independent captions. Ten units occupy five proof pages. The grid, circles and captions are synthetic test fixtures; they are not publication assets. All paths/logs/PDF/INDD/PNG are under ignored `.artifacts/image-layout/runs/<run-id>/`.

The runner uses one host, a single-flight lock and a run-ID-correlated result. It never opens or clears an existing publication. If a lock remains, inspect the existing run/PID before retrying. Native geometry and PDF structural checks do not finalize visual review; open all five rendered proof pages and check circles, crops, left/right association and the rejected H example. Keep the proof's intentional empty worksheet regions separate from judgments about publication page density.
