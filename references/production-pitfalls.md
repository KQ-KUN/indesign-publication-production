# Production corrections learned from real host runs

Load only for the matching correction/audit. These are decision rules, not a
request to migrate approved pages, rewrite prose, or impose one magazine's style.

## Typography: semantic role, actual characters, then rendered lines

- A paragraph named `Editorial`, `Note`, or `Preface` can still function as body
  copy. Establish its role from the source and adjacent text before auditing.
  A style-name count or a correct `leading` value cannot establish correct type.
- Compare paragraph AND character-level effective font family/style, point size,
  leading, tracking, horizontal/vertical scale, baseline shift and justification.
  Resolve mixed values into runs; do not stringify `NothingEnum` as a valid size.
  Check actual consecutive line baselines, excluding paragraph boundaries.
- Correct only unintended differences from the publication's body contract.
  Headings, questions, captions, rosters and credits may have legitimate roles.
  A request for less blank space does not authorize shrinking type or leading.
- Excessive Chinese spacing often comes from justification on a short final or
  forced-break line, tracking overrides, or scaled glyphs. Diagnose those before
  changing text or adding manual spaces. Preserve paragraph/line breaks unless
  a documented display-only change is authorized.
- On a new Word revision, compare main-body changes separately from appendices,
  notes and captions. Keep the user's explicit factual corrections authoritative;
  do not silently restore superseded facts from a newer source file.

## Continuous endings and nearby artwork

- Where sequential two-column endings are requested, disable
  `textFramePreferences.verticalBalanceColumns` on the real ending frame.
  Two equal-height independent single-column frames can also implement manual
  balancing: inspect their bounds, threading and normal body height.
- Do not force columns to look unequal if both naturally fill. An article ending
  with a short right column or an empty right column can be the intended result.
  User-approved endings/section boundaries override the compact-page default.
- Recompose before measuring final baselines. Follow nearby unanchored images,
  captions, colored name plates and shadows when their associated text moves.
  Move existing objects; do not leave obsolete duplicates at their old positions.
- A request to move an image into the left column means BOTH its image frame and
  caption fit inside that column. Check actual frame/graphic bounds, not the
  image center alone. Translate the image-caption unit without resizing/cropping
  if that is all the user asked for. InDesign frame resizing and object translation
  are different operations: verify the graphic transform as well as frame bounds.
- Put media near its event and preferably below the complete related paragraph
  when requested. Pull later prose forward within the authorized flow if media
  would create a void; preserve text order and caption/image association.
- Avoid accidental pure-color parity fillers in continuous electronic editions
  when removal is authorized. Right-hand chapter starts, inside covers and print
  signature padding are separate design/production decisions; do not delete them
  merely because the electronic edition can be shorter.

## Interview divisions and contents credits

- Model an interview as turns/question groups, not isolated formatted paragraphs.
  A single interviewer turn can contain several paragraphs. When asked to remove
  internal separators, override the rule ONLY on continuation paragraphs; retain
  new-turn rules and unrelated interviews. Do not globally alter the question
  paragraph style. Record/assert both removed and retained separator identities.
- In the contents, keep contributor credits in the approved author slot; do not
  push them under titles accidentally. Use the source role (`文/`, interviewer,
  editor, collective author, etc.) and verify one-line fit at the right edge.
  Body copyright attribution and contents authorship are distinct facts.
- Do not apply uncertain factual/spelling corrections to fiction as if they were
  documentary errors. State exactly where a nonfiction inconsistency occurs.

## Native copies, windows and export

- Open approved INDD as a copy. Keep the original and unsaved user work intact.
  A hidden document can pass content checks but has no layout window; do not
  require window focus unless a visible review window exists. Never activate a
  Parent as proof of document output.
- Export facing-page documents through a verified absolute page range. An
  isolated-copy export may need `facingPages=false` to avoid opposite-page bleed
  or incorrect trim; test the actual boxes and neighboring content.
- Distinguish component-local page index, document page name, printed folio and
  final PDF reader-page index. Do not assume a component's Parent footer already
  matches the assembled publication. Native header/footer overlays must be checked
  for the requested folio BEFORE using them; sparse overlay PDFs have empty pages.
  Replace only the identified footer object, not arbitrary matching digits.
- Preserve exact story text and footnotes natively. PDF extraction can reorder
  footer/caption blocks or insert line-wrap whitespace. Compare body text and
  mapped footer/heading regions separately; never strip all numbers or normalize
  away meaningful prose differences to obtain a pass.
- Renamed approved files may be identified by recorded size AND SHA-256 within
  the expected delivery directory. Require one unique match; do not guess based
  on a name, latest timestamp or broad disk search.

## Metadata and distribution variants

- Use the user's/project's author contract; do not hardcode a personal author in
  this reusable Skill. Descriptions, comments and keywords default empty unless
  required. Preserve rights/copyright statements and other required print metadata.
- Native `metadataPreferences.description = ""` has been observed to leave old
  XMP content. For explicit removal use
  `setProperty("http://purl.org/dc/elements/1.1/", "dc:description", "")`, and
  similarly `dc:subject` for keywords. Check the saved/reopened native document,
  then check BOTH PDF Info and root XMP after every final merge/compression.
  Clearing PDF Info alone is insufficient. Handle annotations/comments separately;
  metadata cleanup is not authorization to delete editorial annotations.
- An original-quality PDF and a portable PDF have the same content, layout,
  geometry, page count and back cover. Explain the actual image encoding,
  downsampling and compression differences; do not equate original-quality with
  press-ready. Print output has its own color/profile, bleed and printer contract.
- Prefer reusing an already approved JPEG stream for unchanged image pixels over
  repeatedly recompressing it. Pixel digests differ after lossy compression: compare
  raw-to-raw and portable-to-portable, with explicit source-to-derivative mapping.
  Preserve color space/ICC references, transparency and important small lettering.
  Compression must not rasterize text/vector pages or silently change image crop.
- Assemble only changed pages into the verified latest full issue. Fingerprint
  unchanged pages (content streams plus text/boxes and relevant resource/image
  checks), verify full page count, first/last page and covers, and inspect affected
  pages at normal size. A smaller file or matching image count is not visual proof.

## Source

Adobe documents property removal via an empty `setProperty` value in
[MetadataPreference](https://developer.adobe.com/indesign/uxp/dom/api/m/metadata-preference/).
The other checks above capture observed workflow failures and are conditional
on the current user's layout/content contract.
