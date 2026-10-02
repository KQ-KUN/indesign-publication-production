#!/usr/bin/env python3
"""Fail when current Git changes intersect scopes marked frozen in MODULE_STATUS."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def git_paths(repo: Path, *args: str) -> set[str]:
    output = subprocess.check_output(["git", *args], cwd=repo, text=True, encoding="utf-8")
    return {line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--status", default="workflow/MODULE_STATUS.json")
    args = parser.parse_args()

    repo = args.repo.resolve()
    status_path = repo / args.status
    status = json.loads(status_path.read_text(encoding="utf-8"))
    frozen: dict[str, str] = {}
    for module_name, module in status.items():
        if module.get("frozen") is True:
            for item in module.get("scope", []):
                frozen[item.replace("\\", "/").rstrip("/")] = module_name

    changed = set()
    changed |= git_paths(repo, "diff", "--name-only")
    changed |= git_paths(repo, "diff", "--cached", "--name-only")
    changed |= git_paths(repo, "ls-files", "--others", "--exclude-standard")

    violations: list[dict[str, str]] = []
    for path in sorted(changed):
        for scope, module_name in frozen.items():
            if path == scope or path.startswith(scope + "/"):
                violations.append({"path": path, "module": module_name, "scope": scope})

    print(json.dumps({
        "repo": str(repo),
        "changed_count": len(changed),
        "frozen_scope_count": len(frozen),
        "valid": not violations,
        "violations": violations,
    }, ensure_ascii=False, indent=2))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
