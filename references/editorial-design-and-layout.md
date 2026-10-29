# Editorial Design and Layout

Use this reference for new visual systems, layout refinement, or visual review. It turns aesthetic goals into decisions that can be implemented and verified in InDesign without forcing one house style.

## 1. Establish the design evidence

Use this priority order:

1. explicit user direction and approved artwork;
2. supplied brand guide, design brief, or reference pages;
3. the publication's existing tokens, styles, and accepted modules;
4. content structure, audience, reading conditions, and production format;
5. general editorial-design conventions.

Do not average conflicting references into a vague style. Identify the governing reference and describe any unresolved conflict. Never reopen approved or FROZEN design merely because another treatment might also look good.

## 2. Write a compact visual premise

Before implementing a new system, state the intended effect in a few concrete sentences. Connect editorial character to layout behavior.

Useful dimensions:

- formal, documentary, literary, technical, youthful, archival, or promotional tone;
- fast scanning versus sustained reading;
- quiet continuity versus dramatic section changes;
- text-led, image-led, or balanced pages;
- restrained, expressive, dense, or spacious composition.

A premise is actionable only when it implies choices. For example, "quiet and archival" may imply moderate scale contrast, generous outer margins, restrained color, captions close to evidence images, and few decorative interruptions. It does not automatically imply beige paper, serif type, or any fixed motif.

## 3. Inventory content before choosing geometry

Record the actual element types and their ranges:

- title, deck, author/byline, lead, section heading, body, pull quote, list, note, caption, folio, running head;
- image count, aspect ratios, minimum usable crop, credits, and required associations;
- shortest and longest examples;
- exceptional scripts, formulas, tables, footnotes, or mixed-language passages;
- expected article length and likely page count.

Choose representative stress cases. A system that works only on the opener is not a publication system.

## 4. Build the layout system

### Page geometry

- Confirm trim, bleed, binding, safe area, and facing-page behavior before styling.
- Set margins by function: binding clearance, reading comfort, running furniture, and desired density.
- Treat whitespace as allocated space with a role, not leftover area. Large empty zones are successful only when they reinforce hierarchy and remain balanced across the page or spread.

### Grid and rhythm

- Choose columns from content and measure, not convention. Narrow columns need smaller type or different copy density; wide columns need careful line length.
- Set gutters wide enough to distinguish columns without breaking continuity.
- Use a baseline grid or another explicit vertical rhythm when it improves cross-column and cross-page alignment; do not force every display element onto it.
- Define page families such as opener, continuous text, media-led, section break, and ending. Keep their shared anchors consistent.

### Typographic hierarchy

- Give each semantic role a distinct job. Difference may come from size, weight, family, color, spacing, rule, or position; avoid changing every attribute at once.
- Test body text at actual output size. Evaluate character coverage, Chinese punctuation, Latin/numeral fit, line endings, leading, and paragraph color.
- Judge line length by reading comfort in the actual script and size. Fix poor measure with geometry or type settings, not arbitrary manual line breaks.
- Control widows, orphans, keep options, hyphenation, and heading-to-body attachment through styles.
- Limit families and weights to what the hierarchy needs. Variety is not hierarchy.

### Color and graphic language

- Assign roles: primary text, secondary text, accent, rule, background, and image treatment.
- Preserve sufficient contrast for the intended print stock and output process. Very light tints and hairlines require print-aware checking.
- Reuse a small graphic grammar—rules, blocks, coordinates, contours, markers, or another motif—only when it supports the publication concept. Do not use decoration to fill unresolved space.

### Images and captions

For media geometry, semantic anchoring, page-density diagnosis, and inspected examples, use [image-placement.md](image-placement.md). Diagnose the actual occupied box before changing image scale. New ordinary body-image units use the executable [five-mode geometry contract](image-geometry.md), not arbitrary per-module widths: full-column landscape, centered 2/3-column portrait, equal-frame same-orientation pairs, or same-height mixed pairs with 2:1 widths. Check actual visible content and native objects, preserve source captions/order, and record incompatible protected-image exceptions. These defaults never authorize changing frozen/approved pages.

- Respect approved crops and source restrictions. Do not invent, regenerate, OCR, or replace imagery without authorization.
- Define image behaviors: full bleed, live-area, column width, anchored inline, fixed canvas, or spread.
- Keep captions visually subordinate but readable and unmistakably associated with the correct image.
- Use object styles and fitting rules. Verify effective resolution, links, transparency, crop, and bleed in the actual output path.

### Page and spread rhythm

- Alternate density intentionally. Repeated identical pages feel mechanical; unrelated pages feel accidental.
- Use recurring anchors to create continuity while allowing controlled variation in image scale, section openings, and endings.
- Inspect transitions across spreads, not only isolated pages. Check whether headings, images, and blank space create an unintended stop in continuous reading.

## 5. Implement for revision

- Store reusable geometry, type, color, and spacing in named tokens or style definitions.
- Use Paragraph/Character/Object/Table/Cell Styles as the primary visual API.
- Keep content data separate from visual parameters.
- Use Parent pages for recurring furniture only. Render real content to document pages and return the active view to a document page at the end of a build.
- Prefer threaded frames, anchored objects, span/split-column settings, and keep options over page-specific coordinate patches. When approved flow repeatedly produces poor closing pages, use an explicit content-ID-based layout override for that bounded tail rather than repeatedly shrinking every image. Preserve locked earlier pages and validate their content placement.
- If one page genuinely needs an exception, isolate and name it; do not silently weaken the global system.

## 6. Review in the right order

Review exported pages or a live InDesign document at multiple scales.

### Macro pass

1. At thumbnail scale, can the reader identify openers, sections, body pages, and endings?
2. Is the reading order obvious without reading the copy?
3. Do spreads have intentional balance, density, and variation?
4. Are there accidental voids, crowded zones, or isolated elements?

### Reading pass

1. Is body measure comfortable and consistent?
2. Do leading, paragraph spacing, and indents create a stable texture?
3. Are headings attached to the text they introduce?
4. Are captions associated with their media, and are notes distinguishable from body text?
5. Are widows, orphans, awkward breaks, rivers, stacked punctuation, or overset visible?

### Production pass

1. Confirm trim, bleed, safe area, page side, and binding clearance.
2. Confirm links, image resolution, color space expectations, fonts, transparency, and overprint-sensitive elements.
3. Confirm no hidden layer, nonprinting object, Parent-spread view, or placeholder is being mistaken for final content.
4. Inspect at least the opener, densest page, every distinct page family, each media treatment, and the final page.

## 7. Diagnose and refine

Describe findings as observable relationships:

- "The title and section heading have similar size and weight, so the opener lacks a clear first level."
- "The body begins too low, leaving an unbalanced void even though later text continues."
- "The caption is farther from its image than from the next paragraph, weakening association."

Then change the highest-leverage cause first:

1. reading order and hierarchy;
2. page geometry and grid;
3. density and spacing rhythm;
4. typography details;
5. color and decorative detail.

Change one coherent variable group at a time and compare the same representative pages. Preserve copy and approved assets unless the user explicitly expands the scope.

## 8. Avoid common failure modes

- designing only the first page;
- using oversized titles or decorative lines to compensate for weak structure;
- filling every empty area;
- treating all page types as one template;
- mixing too many typefaces, weights, colors, or alignment axes;
- hard-coding page-specific fixes into shared renderers;
- using screenshots as layout assets when source text or approved artwork exists;
- declaring visual success from static tests, DOM counts, or a single screenshot.
