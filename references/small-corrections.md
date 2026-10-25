# Small publication copy corrections

Use this path for a name, role, date, punctuation mark, a few words, or a narrowly scoped paragraph-format correction (for example four paragraphs losing their first-line indent) in an accepted layout. Global font/grid changes, new manuscripts, new images, or reordered content use module-level validation instead.

## Read and change only what matters

- Inspect current Git changes and the affected source, source map, and build entry. Reuse skill/reference/context already read in this conversation unless it changed; do not dump whole modules or unrelated manuscripts to rediscover a one-line edit.
- Keep the authoritative source and displayed text consistent. Preserve source formatting; prove the requested text delta and record an authorized exception when the original source was locked. Keep the uploaded original if it is provenance.
- Reuse existing correction metadata and validators. Do not create a new task report, hundreds-of-file snapshot, source-specific framework, or repeated test suite for each typo. New tests should protect real failure paths, not mirror the replacement string.
- Batch independent reads/checks and summarize their output. Keep large native reports on disk; print status, changed pages, failures, and timings.

## Choose the least expensive verified execution path

1. If source hash, layout fingerprint, and saved artifact hashes all match the last successful build, reuse that output. Do not start InDesign or re-render it.
2. For changed copy, prefer an existing saved INDD in the already running application. Avoid recreating Foundation styles and Parents when the approved document is usable. Respect unsaved user edits; do not clear or overwrite their document.
3. Use an established in-place correction path if the project has one and it preserves character/paragraph styles, anchored objects, and provenance. Otherwise, recompose the affected module with the existing renderer; do not invent a fragile DOM patch just to claim incrementality.
4. A complete PDF export is often cheap and can remain the deliverable. The expensive raster/visual verification should be limited to affected pages, including downstream pages when text reflows.
5. A targeted formatting change needs native verification, but does not by itself require rasterizing the whole module. Keep the exact paragraph IDs/style delta in the existing map, verify those properties in the host, and compare actual affected pages. Do not alter the locked DOCX for a display-only override.
6. Fall back once to module-level construction when the baseline is absent, layout/source structure changed, or a local assumption fails. Log the reason. An artifact changed outside the verified workflow needs inspection, not an automatic destructive rebuild.

## Validation proportional to the edit

- Always verify exact source-to-story text, including existing authorized display transforms; do not weaken equality or ignore missing content.
- Check document pages, affected frame/story ownership, overset, relevant fonts/links, and final focus on an actual document page.
- Compare native paragraph/line placement to the previous successful report to find affected pages. Unchanged page count alone does not prove unchanged layout. Include old and new page locations and later pages if reflow propagates.
- Render the affected PDF page or region and inspect the requested change. Whole-issue contact sheets, unrelated article runtimes, and repeated all-page high-DPI rendering are unnecessary when the change remains local. Run broader review only for new evidence of broader impact.
- For before/after pixel comparisons use the same renderer, version, DPI, and page boxes. Raster cache keys must include PDF hash, backend/version, DPI and page selection. A new renderer appearing on PATH must not make old cached images appear to be layout regressions.
- Run diff/scope checks once before committing. Use existing frozen-scope checks and the exact changed-file allowlist; preserve unrelated dirty work.

## Time and host lifecycle

- Reuse one healthy host. Never cold-start ordinary and COM instances concurrently.
- Replace a fixed startup sleep with a bounded readiness check when the host supports it. Warm runs should not pay a cold-start delay. Retain the original error stage and stop on failed readiness; do not launch repeated instances.
- Record source preparation, host startup/attach, native layout/export, PDF verification, and rendered-page counts. Separate cold and warm measurements; do not promise a universal runtime or token reduction.
- Stop when the relevant checks pass. Do not re-run the same successful full pipeline without a new change or unresolved concern.

This is a smaller verification scope, not permission to skip native execution for a changed layout or substitute static tests for actual PDF evidence.

Do not classify every layout-fingerprint change as a mandatory full visual sweep: a changed shared grid warrants broad QA; a declared paragraph-local indent warrants native module flow plus changed-page QA. If the existing runner cannot express that distinction, fix its named interface within authorized scope or use its documented full mode; never extract runner source snippets to bypass its initialization and result handling.
