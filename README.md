# InDesign Publication Production Skill

A Codex Skill for editorial design and modular Adobe InDesign/ExtendScript publication work: magazines, journals, commemorative books, catalogs, newsletters, and anthologies.

It focuses on the failure-prone parts of real production repositories:

- editorial art direction, grids, typography, page families, and spread rhythm;
- visual diagnosis and controlled layout refinement;
- narrow manuscript and asset scopes;
- approved/FROZEN component protection;
- deterministic DOCX Paragraph Style mapping;
- Parent spread, story, frame, link, and overset runtime assertions;
- static versus host-runtime versus visual-acceptance boundaries;
- linked external PDF artwork and print geometry;
- minimal staging, reproducible checks, commits, tags, and handoff.

The repository root is the installable Skill directory. `SKILL.md` is the entry point. Supporting references are loaded only when relevant, and `scripts/` contains validation helpers and opt-in image geometry/proof tools.

## How to use

Invoke it explicitly with `$indesign-publication-production`, then provide the publication goal, source files, allowed change scope, existing design authority, and the validation level you want.

Examples:

```text
Use $indesign-publication-production to create a reusable two-column feature layout from this styled DOCX. Establish the grid and typographic hierarchy, implement a thin JSX build, and stop after static validation.

Use $indesign-publication-production to review this exported PDF. Diagnose hierarchy, whitespace, page rhythm, typography, and image-caption association. Do not edit files yet.

Use $indesign-publication-production to refine the current layout without changing copy or approved artwork. Keep frozen modules untouched and validate the representative pages in InDesign.

Use $indesign-publication-production to debug this InDesign build: text frames exist but the active view shows a blank Parent spread. Preserve the visual design and add runtime assertions.
```

The Skill can also be selected automatically when a request clearly concerns InDesign publication design or production. A useful request states:

- what is being designed or repaired;
- which files or modules are in scope;
- which artwork, references, or layouts are already approved;
- whether InDesign/GUI runtime checks are allowed;
- whether the desired result is implementation, visual review, refinement, freeze, or assembly.

## Validation helpers

```powershell
python scripts/check_frozen_scope.py D:\path\to\publication-repo
python scripts/inspect_pdf_artwork.py cover.pdf --trim-mm 185 260 --bleed-mm 3
```

Both scripts above are read-only. The PDF helper requires `pypdf`.

New ordinary body images follow the [five-mode column geometry contract](references/image-geometry.md). `scripts/image_layout.py` computes shared frames and checks observed native geometry; Pillow inspects real alpha bounds. The optional proof uses pypdf/pypdfium2 and a real InDesign host, creates only a new diagnostic document, and writes under ignored `.artifacts/`:

```powershell
python scripts/image_layout.py plan request.json --out plan.json
python scripts/image_layout.py validate plan.json native.json --tolerance 0.5
powershell -File scripts/run_image_layout_demo.ps1 -Python python
```

The proof includes five modes, unequal-aspect cropping, a trimmed portrait and an intentionally rejected padded-canvas negative. Inspect its five rendered pages before claiming visual acceptance. No approved publication is migrated automatically.

Run the included tests with:

```powershell
python -m unittest discover -s tests -v
```

## License

MIT
