# Image placement: editorial evidence before scale

Read for photographs, archival images, posters, logos, portraits, book covers, or unexplained blank regions. Explicit user restrictions and approved pages govern; the default geometry applies to new ordinary body images, not retroactive changes to approved pages.

## Default geometry before visual refinement

Use the five-mode calculator and actual-DOM validator in [image-geometry.md](image-geometry.md). Defaults: a single landscape fills W; a centered portrait uses 2W/3; two same-orientation images share equal widths/heights; mixed landscape/portrait frames share a height with widths 2(W-G)/3 and (W-G)/3. Read the contract for grid gaps, visible-content checks, crop/stretch limits and structured exceptions. Do not choose widths ad hoc from historical size suggestions.

## Diagnose what actually occupies the page

Before saying “make it smaller/larger”, distinguish:

1. source pixel dimensions and visible content bounds (including alpha margins or scanned paper);
2. placed graphic bounds, frame bounds, crop and transform;
3. anchored-object reserved height, paragraph leading/space and wrap offsets;
4. keep chains, column/page breaks and frame threading;
5. the related source paragraph, year/event and caption.

A portrait cover inside a wide transparent canvas can reserve an entire horizontal block while the visible cover stays tiny. Remove only authorized outer transparent padding into a derivative asset and retain the original; do not crop white paper or printed content automatically. Record both visible-art and layout bounds. Enlarging the padded canvas or merely changing ABOVE_LINE to another anchor does not address the cause.

## Select a treatment from content and reading order

| Content/job | Prefer | Check before changing scale |
| --- | --- | --- |
| Documentary/history evidence | Default column geometry near complete event paragraphs, unless an approved archival exception governs | Year ownership, original sequence, readable evidence, current-column space |
| Portrait poster/book cover | Real portrait asset at 2/3 column width, centered; protected content may require an exception | Effective resolution, embedded lettering, real alpha bounds, no huge invisible canvas |
| Two related portrait covers | Side-by-side within ONE column, original proportions and small gutter; shared caption only if supplied/authorized | Combined width including gutter; legibility at actual size; source caption/order preserved |
| Several event photographs | Ordered stack or small aligned group within the permitted column | Group does not silently become page-wide; unequal heights do not create unusable slivers |
| Main character/hero visual | Give the silhouette adequate vertical room inside its assigned column | Visible body, not empty transparent margins, is the visual anchor; preserve copy column and aspect ratio |
| Image-led feature/opening | A deliberately larger treatment if the brief permits | Does not override a text-led/history single-column restriction |

### New defaults versus approved Shan exceptions

New ordinary body-image units use the column-relative rules above. The former blanket starting suggestions “photos 50–65mm / posters 38–50mm / marks 25–38mm” are superseded and must not override them.

Existing approved Shan History layouts remain protected: all images/groups within one column, source order/year ownership and existing captions preserved, with previously approved small archival displays and bounded tail layouts retained as explicit legacy exceptions. This Skill update neither deletes that contract nor authorizes reflowing locked pages. When future History work is explicitly requested, apply defaults to the authorized new/redesigned units and record any retained protected/low-resolution exception; do not silently migrate the whole chapter.

Ordinary images use proportional cover fitting with safe crop review. Only a mixed pair's ordinary landscape member can use the documented, bounded nonuniform-stretch option; it never applies to emblems, logos, QR codes, important text, archives or faces. Preserve originals, effective resolution, factual content and semantic anchors. If safe fit cannot meet the default, report a named exception. Do not AI redraw or upscale nonexistent detail. See [image-geometry.md](image-geometry.md) for executable safeguards.


## Semantic anchors and small keep units

- Key placements to stable source paragraph/image/event IDs, not guessed PDF page numbers. Preserve the source and use a display/layout sidecar for exceptions.
- Put evidence images before or after a COMPLETE paragraph. Resolve a legal insertion point after checking collection length; never split the last words of a sentence to fit an anchor. An intentional image beside text must still leave the story in its original order.
- Keep image and its existing caption together as the smallest useful unit. Do not chain that unit to all following media or the next year heading. Year headings keep the next text; preceding images do not inherit that keep.
- Inline/above-line is appropriate when its real box fits the column; custom anchors or local frames are alternatives when wrap and reserved space have been verified. Choose on observed geometry, not a blanket preference for one anchor enum.
- Re-resolve paragraph/group/graphic specifiers after each placement/recomposition. Assert successful group creation before reading anchored settings. Record image ID, source paragraph, anchor, frame/graphic bounds, page/column, crop, scale and caption association in the existing native report.

## Correct density without oscillating redesign

1. Inspect the sparse/crowded page AND its neighboring spread, using the same renderer/DPI before and after.
2. Find the first constraint causing the void: oversized box, transparent padding, keep chain, forced break, large group, disconnected frame or genuine semantic boundary.
3. Change that cause locally. For a new default unit keep the required widths: adjust insertion position, safely solve/crop its height, or move the complete unit forward. For approved legacy small-image layouts retain their contract. Any new width exception needs a recorded reason; keep captions readable. Do not shrink all images, reduce body type, force an arbitrary page count or expand artwork solely to fill white space.
4. Preserve a few related visual sizes/alignment axes. Allow purposeful whitespace; no fixed coverage percentage proves good design. Review actual reading continuity and why each blank region exists.
5. If a bounded tail repeatedly oscillates under automatic flow, stop global compression. Use a named tail override keyed to its events with explicit frames/column assignments and consistent source sequence. Compare/fingerprint locked earlier pages. Limit design candidates to a small coherent set, inspect a representative page, then apply the chosen rule; do not send repeated full exports without a changed hypothesis.

Remove an extra terminal page only after proving it contains no visible module text, image/caption, anchored item or intentional parity/transition content, and deletion leaves no overset or missing source. A low-density ending is a design review; an actually empty accidental trailing frame/page is a flow bug. Never delete a page just to reach a target count.

## Inspected publication cases

These are local reference observations, not templates or image assets to copy. Page numbers below are **1-based PDF pages**, not printed folios. Supplied source directory: the user-provided reference-magazine folder. If files are absent later, the observations remain usable; do not require an unrelated machine to recreate this directory.

| Source | PDF pages inspected | Observed relationship | Apply / boundary |
| --- | --- | --- | --- |
| 《无理数》北理工科幻社2025年纪念社刊（带祝福语版） (1).pdf | 20 (printed 14) | Two small circular badges sit within the left text column with short captions; the other column keeps continuous interview copy | Small evidence can suffice. Do not copy the publication's rules or page furniture. |
| Same | 67 (printed 61) | A portrait comic cover sits below introductory copy in the left column; continuous review occupies the right column | A real portrait image needs its own proportions, not a landscape placeholder canvas. This opener has its own deliberate whitespace and is not a default History page. |
| Same | 85 (printed 79) | Two columns interleave related event photographs, compact captions and prose | Group by event and keep captions close; do not collect every photograph into a detached image page. |
| 《象限》航理师开四校幻协联合社刊-2026年9月第一版.pdf | 106 (printed 102), 109 (printed 105) | Two portrait book covers share the width of ONE column, with common caption below; text continues alongside/around the group | Two images need not mean two-column span. Preserve the source's actual caption contract. |
| Same | 52 (printed 48) | A large horizontal ending illustration spans the article's lower width | Useful contrast case: deliberate image-led closure, not a reason to make History evidence span columns. |
| 临界点30周年纪念（电子版）(1).pdf | 29 (printed 18) | Activity text and photographs are interspersed across two columns; each photograph occupies its own column and has a close caption | Good documentary rhythm comes from semantic interleaving, not uniform giant image blocks. |
| Same | 14 | A paired image band above the body is an intentional interview opening | Page-family-specific wide treatment; do not import into a locked single-column archive. |
| Same | 38 (printed 27) | Multiple dining/event pictures form an image-led collage under two short text columns | Topic-specific dense collage. Do not adopt its colored framing, angled crop or collage system for Shan History. |

Audit evidence: the three source PDFs contain 116, 163 and 88 pages respectively. Low-resolution overviews were used to select the nine detailed pages listed above. Inspection is not a claim that every full-size page was reviewed or that the reference publishers' native InDesign settings are known.

## Native and rendered acceptance

Preserve complete text, image count/order, captions and semantic ownership. Check native link/font/overset status, actual document-page visibility and non-distorted placement. Inspect the exported affected page and neighbor at normal reading size: visible art size, sentence continuity, caption attachment, unplanned voids, overlap and later-page effects. A successful script, matching image count, small file size or “no overset” alone does not prove good layout. After a local change, raster only affected/reflowed pages; a global placement-policy change warrants each distinct media treatment plus dense and ending pages. Documentation-only changes need no host. Calculator/adapter changes use the independent host proof when authorized and available.
