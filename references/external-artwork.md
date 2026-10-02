# External PDF artwork integration

Read this reference when a user supplies an approved PDF cover, insert, plate, advertisement, or other complete artwork.

## Source-of-truth boundary

- The approved PDF is a single artwork object, not a source for recreating text, texture, logos, or lines in InDesign.
- Keep prior generator code as history when requested, but mark it superseded and ensure Assembly no longer calls it for that artwork.
- Place the complete PDF as a linked asset and preserve proportions and link status.

## Inspect before writing

Use a structural PDF tool such as `pypdf` or `pdfinfo -box` to record:

- page count and rotation;
- MediaBox, CropBox, TrimBox, BleedBox, and ArtBox in points and millimetres;
- encryption and PDF version;
- SHA-256;
- embedded image/object inventory when a transformation is proposed.

Render for visual comparison when geometry or content is modified. Structural extraction alone does not prove visual equivalence.

The included `scripts/inspect_pdf_artwork.py` performs read-only page/box/hash checks.

## Geometry mismatch

If the supplied PDF does not match the required trim/bleed geometry:

- without explicit resizing authorization: stop, report actual geometry, and do not integrate it;
- with authorization: normalize page geometry without reconstructing the artwork.

Prefer a uniform scale plus centered crop/letterbox decision based on the user's print requirement. Record the scale, translation, and crop. Never silently use independent X/Y scaling.

Example only: a `185 x 260 mm` finished cover with `3 mm` bleed normally uses:

- MediaBox/CropBox/BleedBox: `191 x 266 mm`;
- TrimBox: `[3, 3, 188, 263] mm`.

Do not impose those values on a project with a different trim or printer specification.

## Preserve artwork fidelity

- Do not rasterize a PDF to change its dimensions.
- Prefer a page transformation that keeps existing resource objects and wraps/transforms page content.
- Compare source and target embedded image names/counts/data sizes where meaningful.
- Render source and target at equivalent pixel height and inspect for clipping or shifts.
- Retain the original source outside the repository when the repository should contain only the normalized final asset.

## Repository record

Record:

- final linked asset path and hash;
- actual page and trim/bleed geometry;
- direct-placement instructions for Assembly;
- `APPROVED / EXTERNAL_ARTWORK` for the approved component;
- independent `PENDING` or `WIDTH_PENDING` states for unresolved components;
- any historical renderer marked `SUPERSEDED_BY_EXTERNAL_ARTWORK`.

Approval is component-specific. A front-cover approval does not authorize generating or approving a back cover or spine.
