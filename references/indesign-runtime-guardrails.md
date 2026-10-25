# InDesign runtime guardrails

Read this reference when creating or modifying JSX builds, renderers, Parents, threaded stories, media placement, or runtime assertions.

## Document page versus Parent spread

- `parents.create()` and Parent spread editing may leave the active window on a Parent.
- A blank active Parent spread is not evidence that DOCX import, renderer execution, or story writing failed.
- Treat `document.pages` and `masterSpreads`/Parent spreads as different domains.
- At the end of every build that creates or edits Parents, call `focusDocumentPage()` or equivalent and target the first generated document page.

## Assert data, not the current screen

At minimum, runtime assertions should cover the parts relevant to the module:

- expected document page count and page dimensions;
- `textFrames > 0` and at least one frame intersecting a real document page;
- visible layer and frame state;
- story/visible character count;
- exact critical first and last text;
- expected Paragraph Style counts;
- linked graphics/media existence, page ownership, dimensions, and visibility;
- explicit overset result;
- automatic continuation/no-progress protection for threaded flow.

Keep assertions module-local. Do not concatenate all `doc.stories` and count a local phrase: running headers and Parent stories can legitimately duplicate it.

## Defensive DOM collection access

InDesign DOM properties may be arrays, array-like values, or collections depending on the host and object.

For `allGraphics` and similar values:

1. try bracket access (`value[0]`) when it is array-like;
2. call `value.item(0)` only when `item` is actually a function;
3. fall back to the concrete frame collection such as `graphics` when appropriate;
4. if the graphic object is unreliable, validate the containing frame geometry without deleting the existence/link assertion.

Never write `allGraphics.item(0)` as an unconditional assumption.

## Threaded flow

- Create a deterministic first frame and thread continuation frames in document-page order.
- Detect overset after each placement/flow step.
- Add a no-progress guard so a layout cannot append pages forever when text does not move.
- Span only the Paragraph Styles explicitly contracted to span columns.
- Use host Paragraph Styles as the structural source of truth; avoid text heuristics.

## Encoding and compilation

- New or modified JSX must use UTF-8 BOM.
- Verify `#include` paths in native compilation because Node parsing cannot validate ExtendScript include resolution or InDesign DOM names.
- Keep Unicode paths in mind: a compile pass does not prove that `place()` can open the file in the host.

## Acceptance language

- Static source tests: “static checks passed.”
- Native compilation: “compiled in the InDesign host.”
- Successful script run with assertions: “runtime checks passed.”
- Human/visual confirmation: “visually accepted.”

Do not collapse these into one claim.

## Small corrections and cached evidence

For local copy edits use [small-corrections.md](small-corrections.md). Reuse a saved approved document and one healthy host; avoid fixed cold-start waits on warm runs. Keep exact source/story and overset checks, but render only changed/reflowed pages. A source/layout/artifact fingerprint match can reuse unchanged output without host execution. Distinguish renderer/version/DPI in raster cache keys; never compare mixed-backend cache images as a layout defect. Do not overwrite unsaved user work or fall back repeatedly.


## Single-flight builds, timeouts, and trustworthy results

- Use one project runner and one healthy host. Preserve its initialization, scope, exit-code checks, and result contract. Do not read a PowerShell runner into a string and execute extracted substrings: child-scope assignments can vanish, timing variables can be uninitialized, and a successful native build can be misreported as failed.
- A tool returning a live session/cell ID is a running job, not a failed build. Resume that exact ID. A client wait timeout is not proof that `DoScript`, export, or rendering stopped. Check the existing PID, current stage, output modification time and run ID before another dispatch. Never launch the same build concurrently to recover a timeout.
- Separate startup/readiness, script execution, export, PDF verification, and tool transport. Measure their durations separately. Use bounded waits/backoff; an unchanged poll merits no new progress claim. Keep commentary concise while a long job continues.
- On an unresponsive host, inspect modal dialogs/readiness and the last stage before retrying. Do not kill a host with unsaved work, delete preferences, reset ACLs, or edit registry settings merely because startup/COM failed. One scoped recovery attempt is enough; a repeated identical failure needs a new diagnosis, not another launch.
- Existing runners should return a structured result or reliable exit code, with stage/error context. Where a persistent result file is used, correlate it to the current request (run ID or verified request/output timestamps and input hashes). An old `PASS` file does not prove the current request succeeded.
- Distinguish `native PASS + wrapper failure` from `native FAIL`. After a wrapper failure, first establish whether the intended output was already generated correctly. Repair the wrapper, then rerun only the unresolved verification; do not repeat a successful layout/export without a concrete reason. Never manually promote an incomplete or failed machine check to PASS.
- Observe approval/sandbox results before dependent operations. If a command was rejected, none of its claimed outputs are evidence. Separate verification, staging/commit, and push so their outcomes remain reviewable; do not bundle a manual PASS edit with publication.

## Original error location and object context

A top-level catch must preserve stage, original name/message/file/line, optional source, stack, and module-local context (image index/source paragraph/anchor/frame label). Write the diagnostic before displaying an alert. Do not finish with bare `throw e`: the host may replace the actionable location with the catch/rethrow line. Keep the partial document for inspection; report failure through the runner contract.

Resolve DOM chains into checked locals. Validate paragraph, collection length, insertion point, placed item/group, anchored settings, and page/story ownership before dereferencing them. Re-resolve concrete specifiers after anchoring/recomposition. Do not assume `.item(-2)` is a valid end-of-paragraph anchor, a graphic always has `parentPage`, or a line always has `parentTextFrames`.

If a paragraph has lines but zero owning frames, resolve it again after recomposition and inspect actual story/frame contents and overflow before deciding. Do not delete an overset assertion or ignore the paragraph to suppress a suspected false positive. Use tolerances for geometry; advisory aesthetics/page targets are not fatal assertions.

Compile against ExtendScript's supported syntax (including reserved identifiers such as `final`); modern Node parsing is not sufficient. Check parser matches before taking `[1]` and include the offending token/source location in failure reports. Preserve UTF-8 BOM for JSX.

## Stop conditions and proportional verification

- Stop after the relevant source, native, rendered-page, and scope checks pass. Reuse that evidence unless inputs changed or a concrete unresolved defect justifies more work.
- Use source + visual-contract + saved-artifact fingerprints. A no-change cache hit needs no host. A source-count match alone is not a cache hit or an integrity check.
- Compare local paragraph formatting/geometry as well as text when detecting affected pages; a zero-indent change can keep the same line text and baselines. Follow downstream reflow, not a fixed page number.
- Keep full native diagnostics on disk and return status, changed pages, timing and failure context to chat. Do not dump the complete source, all names, all pages or whole logs after every small correction.
