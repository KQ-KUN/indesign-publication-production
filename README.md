# InDesign Publication Production Skill

An Agent Skill for editorial design and modular Adobe InDesign/ExtendScript publication work: magazines, journals, commemorative books, catalogs, newsletters, and anthologies.

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

## Platforms and desktop clients

The package uses standard `SKILL.md` frontmatter and relative resources. It can be
loaded by Agent Skills clients including DeepSeek DSH and Kimi; actual local tool
permissions must be checked in each desktop build. The workflow has no Codex-only
execution dependency. See [installation and compatibility](references/platforms-and-clients.md).

- **Windows:** automatic registered-version/process discovery and PowerShell COM adapter.
- **macOS:** bundle-version/process discovery and AppleScript adapter; requires Automation consent.
- **Linux/WSL/containers:** static/PDF validation and transfer to a Windows/macOS host.

```text
python scripts/indesign_runtime.py detect
python scripts/indesign_runtime.py run scripts/runtime_probe.jsx --expect-prefix "PASS "
python scripts/indesign_runtime.py status <returned-job-directory> --wait-seconds 10
python scripts/package_skill.py --out .artifacts/indesign-publication-production.zip
```

Use Python 3.10+ (`python3` on systems where appropriate). No application is launched
by detection; cold launch is explicit with `--allow-launch`. A running receipt is
resumed with `status`, not rerun. `COMPLETED` means the host returned, not that a
publication is visually approved. Version hints select candidates; `app.version`
and executable identity verify the attached host. Run only authorized JSX scripts.

Project installation shared by DSH/Kimi: place this whole folder at
`.agents/skills/indesign-publication-production/`. Kimi Work also provides local
Skill import; verify the particular UI/import format. Plain chat/web modes without
local tools can prepare work but cannot run local InDesign. Platform/client status
must distinguish documentation, fixture coverage and actual host/client tests.

[Production correction rules](references/production-pitfalls.md) cover character-level
typography, image/caption alignment, sequential endings, interview turns, complete
issue assembly, metadata and distribution variants. Existing local layout contracts
remain authoritative.

## How to use

Use the client's Skill picker (Codex: `$indesign-publication-production`; Kimi Code: `/skill:indesign-publication-production`), or ask the agent to load `SKILL.md`, then provide the publication goal, source files, allowed change scope, existing design authority, and the validation level you want.

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

Run the included tests with (Python 3.10+):

```powershell
python -m pip install -r requirements-test.txt
python -X utf8 -m unittest discover -s tests -v
```

## License

MIT

## Verification status

As of 2026-11-11: Windows native discovery and read-only JSX dispatch verified on
InDesign 21.5.1.73 / Python 3.13.5. Unit tests cover version selection, macOS plist
and process fixtures, Linux fallback, job resume/locking, source mutation and
explicit distribution filtering. CI tests Python 3.10/3.13 on Windows/macOS/Linux;
it does not install InDesign or validate desktop-client UI integration.

macOS native execution, additional InDesign versions, and real DSH/Kimi desktop
Skill load/command invocation still require tests on those environments. These are
implemented/documented routes, not claimed native/client acceptance. No private
publication files or generated diagnostics are distributed in this repository.
