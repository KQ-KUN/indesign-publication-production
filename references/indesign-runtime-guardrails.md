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
