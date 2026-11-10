"""Package public Skill resources; omit repository internals and generated artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def public_files(root: Path) -> list[Path]:
    names = json.loads((root / "distribution-files.json").read_text(encoding="utf-8"))["files"]
    if not isinstance(names, list) or not names or any(not isinstance(name, str) for name in names):
        raise ValueError("Distribution manifest must contain explicit public relative paths.")
    files = []
    for name in names:
        relative = Path(name)
        if relative.is_absolute() or "\\" in name or any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
            raise ValueError("Invalid distribution path: " + name)
        path = root / relative
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Distribution file escapes Skill directory: " + name)
        files.append(path)
    return sorted(set(files))


def package(root: Path, output: Path) -> dict:
    files = public_files(root)
    if any(not p.is_file() or p.is_symlink() for p in files):
        raise ValueError("Missing public file or symlink; inspect package input.")
    if output.resolve() in [p.resolve() for p in files]:
        raise ValueError("Package output must not overwrite a public source file.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(root).as_posix())
    return {"file": str(output), "files": len(files), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(ROOT, args.out), ensure_ascii=False, indent=2))
