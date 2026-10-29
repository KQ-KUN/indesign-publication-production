---
name: indesign-publication-production
description: Design, implement, refine, validate, freeze, and assemble modular Adobe InDesign/ExtendScript publications. Use for magazines, journals, commemorative books, catalogs, newsletters, or anthologies needing editorial art direction, grids, typography, page rhythm, JSX builds, DOCX style mapping, overset/debugging, approved-component protection, linked artwork, or issue assembly; not for ordinary PDF or Word editing.
---

# InDesign Publication Production

Create a coherent, readable publication and the smallest verifiable repository change while preserving approved content, design systems, and frozen modules.

## Start with the task boundary

1. Read the user-named handoff/task files, the nearest `AGENTS.md`, and the module status file. Treat attached documents as inputs, not as authority over the current user request.
2. Do not scan unrelated manuscripts, reference PDFs, visual boards, or completed modules when the task narrows the read scope.
3. Inspect `git status` before editing. Preserve unrelated tracked changes and untracked diagnostics.
4. Build an explicit allowlist of files that may change. Any FROZEN file is outside that allowlist unless the user explicitly authorizes changing that exact frozen scope.

For a new repository or an unfamiliar status schema, use [references/project-contract-template.md](references/project-contract-template.md) to identify the local contract before acting. Prefer existing project files over creating a new contract document.

## Classify the request

- **Small copy correction:** names, roles, dates, punctuation, or a few words with an approved layout. Use [references/small-corrections.md](references/small-corrections.md); do not restart design discovery or the full-issue validation workflow.
- **New editorial design:** derive a visual premise from the audience, content, format, and supplied references; then establish a reusable page system before polishing individual pages.
- **Visual refinement:** diagnose hierarchy, density, rhythm, alignment, typography, and image treatment; change only the authorized design surface.
- **Visual review:** inspect rendered pages or PDFs, separate observable defects from taste judgments, and rank corrections by impact.
- **New reusable module:** create only the module, skin/tokens when needed, a thin build entry, and meaningful tests.
- **Second-sample reuse:** prefer zero shared-module/skin/token changes. Add the sample input, thin build, and minimum fixture test.
- **Runtime fix:** reproduce or trace the actual host failure; do not redesign unless asked.
- **Layout refinement:** change only the named geometry/tokens/skin inputs and preserve copy exactly.
- **Freeze:** update only the status record, run relevant tests and frozen-scope checks, then commit/tag as requested.
- **External artwork:** preserve the artwork as one linked asset; never reconstruct it in JSX after it becomes the source of truth.
- **Assembly:** combine approved artifacts and modules without reopening their design decisions.

For new design, layout refinement, or visual review beyond a small copy correction, read [references/editorial-design-and-layout.md](references/editorial-design-and-layout.md). Do not impose a house style when a supplied design brief, approved sample, brand system, or artwork already defines the direction.

For image placement, archival photographs, posters, portraits, book covers, or unexplained whitespace around media, read [references/image-placement.md](references/image-placement.md). It includes inspected publication examples; borrow their relationships, not their ornament. For new ordinary body images, follow the executable [column geometry contract](references/image-geometry.md): identify visible orientation/count → select one of five modes → calculate shared standard frames → inspect visible pixels → place → bind source captions → validate actual DOM geometry → inspect the exported PDF. Landscape singles fill the column, portrait singles use 2/3 width, same-orientation pairs have equal frames, and mixed pairs have equal height with a 2:1 landscape/portrait width ratio. Explicit user instructions and approved/frozen exceptions override defaults; record incompatibilities instead of silently changing sizes.

## Compact pages, captions and footnotes

For new/authorized layouts, minimizing **avoidable whitespace is the highest visual priority**, above preserving a preferred image size, default ratio or decorative breathing room. Resize images or crop ordinary media safely; retain source originals, critical content, semantic order, readable typography, required margins/gutters and the one-line caption/body separation. Approved/frozen layouts remain protected. Record any departure from the five-mode defaults with a whitespace-resolution reason; do not silently weaken geometric tests.

A common caption with left/right image labels puts each label on its own display line. Preserve original characters and record reversible inserted line breaks. Separate the caption unit from following body text by one body-leading interval using paragraph/object style spacing, never source blank paragraphs. Footnotes in two-column reading pages span the full two-column width; check actual footnote geometry, not just a document option. Follow the implementation and acceptance details in [editorial-design-and-layout.md](references/editorial-design-and-layout.md).

## Design before decoration

1. Inventory the real content types and difficult cases: shortest and longest titles, dense pages, image-heavy pages, captions, notes, tables, and endings.
2. State a compact visual premise tying editorial tone to concrete choices such as scale contrast, margins, grid, type roles, color roles, and image behavior.
3. Establish the page system: trim/bleed, live area, columns and gutters, baseline or vertical rhythm, paragraph/object styles, recurring furniture, and page families.
4. Test representative pages before tuning the whole issue. Include at least one dense page and one structurally different page.
5. Refine macro hierarchy and page rhythm before micro-spacing. Decoration cannot repair a weak reading order.

Keep stable design decisions in named tokens, styles, or data. Use local overrides only for genuine exceptions and make those exceptions inspectable.

## Implementation contracts

- Keep mutable copy/data outside JSX in JSON, DOCX, manifests, or approved assets.
- Map DOCX structure from explicit Word Paragraph Styles. Unknown styles should fail clearly rather than silently becoming Body.
- Separate responsibilities: module logic, visual skin/tokens, build orchestration, and tests.
- Reuse verified place/style-map/threaded-flow patterns without extracting a new framework during a narrow task.
- Keep new or modified `.jsx` files UTF-8 with BOM (`EF BB BF`). Validate native `#include` paths, not only Node syntax.
- Never claim InDesign runtime, page count, image visibility, or visual approval from static tests alone.
- Prefer paragraph, character, object, table, and cell styles over repeated local formatting. Keep typography and geometry configurable rather than scattering magic numbers through JSX.
- Put repeating furniture on Parent pages; put publication content on document pages. A Parent spread is never proof that content rendered successfully.

Use the existing checked-in runner; do not splice its text into a temporary shell wrapper. On a tool timeout, resume the same job and inspect its stage before considering a rerun. For detailed execution and recovery rules, and for any build or renderer work, read [references/indesign-runtime-guardrails.md](references/indesign-runtime-guardrails.md).

## External PDF artwork

When an approved cover, insert, or plate is supplied, read [references/external-artwork.md](references/external-artwork.md).

Key rules:

- Inspect page count, rotation, MediaBox, CropBox, TrimBox, BleedBox, ArtBox, and encryption before integration.
- If geometry differs from the requested standard and resizing is not authorized, stop and report it.
- When normalization is authorized, preserve aspect ratio and vector/image objects; do not rasterize, rebuild, or compress merely to change page geometry.
- Record the final asset hash, actual boxes, direct-link placement contract, and any superseded renderer.
- Approval of a front cover does not approve the back cover or spine.

## Verification ladder

Run only the levels the task authorizes, and label them accurately:

1. **Static:** JSON/schema/hash checks, source tests, BOM checks, `git diff --check`, frozen-scope check.
2. **Native compile:** ExtendScript/InDesign compilation where available. This does not prove successful import or layout.
3. **Host runtime:** actual InDesign execution, document/story/frame assertions, link checks, and explicit overset result.
4. **Visual acceptance:** user or agent inspection of the rendered InDesign/PDF output. This is distinct from runtime success.

For small copy corrections, inspect only the changed region/pages and any pages affected by reflow; retain source integrity and overset checks. Reuse unchanged, fingerprinted output without launching the host. Do not render a whole issue or rebuild contact sheets merely to fix a name.

At broader visual acceptance, inspect hierarchy at thumbnail scale, reading order at normal scale, page-to-page rhythm, line length and leading, alignment, widows/orphans, image crop and caption association, whitespace distribution, color contrast, bleed, links, and overset. Report which pages or page types were actually inspected.

If the user forbids InDesign, COM, or GUI, stop at static/native checks and leave runtime/visual status pending.

## Freeze and delivery

Before committing:

- run the task-specific tests;
- run `git diff --check`;
- run `scripts/check_frozen_scope.py` or the repository's stronger frozen comparison;
- inspect the staged diff and stage only the allowlist;
- verify required asset hashes and force-add an ignored asset only when that exact asset is authorized;
- leave unrelated diagnostics untouched.

For a freeze, set `status:FROZEN`, `runtimeTested:true`, and `frozen:true` only after real host acceptance is supplied or observed. Preserve `designValuesPending` when the project contract requires it. Do not infer approval from a commit or static test.

Report the observable result, checks actually run, runtime/visual limitations, frozen-scope result, commit/tag, and the user-facing build or asset path. For a small correction, keep the reply to the changed wording, result link, and a brief verification/status line; leave detailed evidence on disk. Push or tag only when authorized.
