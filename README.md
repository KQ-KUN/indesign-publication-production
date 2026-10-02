# InDesign Publication Production Skill

A Codex Skill for modular Adobe InDesign and ExtendScript publication work: magazines, journals, commemorative books, catalogs, newsletters, and anthologies.

It focuses on the failure-prone parts of real production repositories:

- narrow manuscript and asset scopes;
- approved/FROZEN component protection;
- deterministic DOCX Paragraph Style mapping;
- Parent spread, story, frame, link, and overset runtime assertions;
- static versus host-runtime versus visual-acceptance boundaries;
- linked external PDF artwork and print geometry;
- minimal staging, reproducible checks, commits, tags, and handoff.

The repository root is the installable Skill directory. `SKILL.md` is the entry point. Supporting references are loaded only when relevant, and `scripts/` contains read-only validation helpers.

## Validation helpers

```powershell
python scripts/check_frozen_scope.py D:\path\to\publication-repo
python scripts/inspect_pdf_artwork.py cover.pdf --trim-mm 185 260 --bleed-mm 3
```

Both scripts are read-only. The PDF helper requires `pypdf`.

Run the included tests with:

```powershell
python -m unittest discover -s tests -v
```

## License

MIT
