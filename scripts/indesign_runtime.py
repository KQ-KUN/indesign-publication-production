"""Client-neutral InDesign discovery and single-flight JSX execution (Python 3.10+).

Detection never activates COM or launches InDesign. Run receipts survive client
timeouts; inspect the same job with `status`, rather than dispatching it again.
Only the Python standard library is needed. No model API keys or network service.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
TERMINAL = {"COMPLETED", "FAILED"}


class RuntimeFailure(Exception):
    pass


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic_json(path: Path, value: dict) -> None:
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, text=True, encoding="utf-8-sig", errors="replace", capture_output=True, **kwargs)


def windows_executable(command: str) -> str:
    """Parse registered LocalServer32 without evaluating a shell command."""
    command = os.path.expandvars(command.strip())
    match = re.match(r'^"([^"]+\.exe)"|^(.+?\.exe)(?:\s|$)', command, re.I)
    return (match.group(1) or match.group(2)) if match else ""


def powershell() -> str:
    # Windows PowerShell exposes Marshal.GetActiveObject; pwsh/.NET may not.
    path = shutil.which("powershell.exe")
    if not path:
        raise RuntimeFailure("Windows PowerShell 5.1 is unavailable; use the Scripts panel or a verified bridge.")
    return path


def windows_inventory() -> tuple[list[dict], list[dict], list[str]]:
    import winreg
    candidates, warnings = [], []
    for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "", 0, winreg.KEY_READ | view) as root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                name = winreg.EnumKey(root, i)
                if not re.fullmatch(r"InDesign\.Application(?:\.\d+(?:\.\d+)*)?", name, re.I):
                    continue
                try:
                    with winreg.OpenKey(root, name + "\\CLSID") as key:
                        clsid = winreg.QueryValue(key, "")
                    with winreg.OpenKey(root, "CLSID\\" + clsid + "\\LocalServer32") as key:
                        path = windows_executable(winreg.QueryValue(key, ""))
                    if path and Path(path).is_file():
                        candidates.append({"id": name, "path": str(Path(path).resolve()), "version_hint": name.removeprefix("InDesign.Application."), "backend": "windows-com"})
                except OSError:
                    continue
    script = "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); @(Get-Process InDesign -ErrorAction SilentlyContinue | ForEach-Object { [pscustomobject]@{pid=$_.Id;path=$_.Path} }) | ConvertTo-Json -Compress"
    result = execute([powershell(), "-NoProfile", "-NonInteractive", "-Command", script], timeout=20)
    if result.returncode:
        raise RuntimeFailure("Unable to enumerate InDesign processes: " + result.stderr.strip())
    running = json.loads(result.stdout or "[]")
    if isinstance(running, dict):
        running = [running]
    if any(not item.get("path") for item in running):
        warnings.append("An InDesign process path is unreadable; execution must wait for unambiguous identity.")
    # Prefer version-specific registrations, without a fixed release/year list.
    unique = {item["id"]: item for item in candidates}
    candidates = list(unique.values())
    versioned_paths = {os.path.normcase(c["path"]) for c in candidates if c["id"] != "InDesign.Application"}
    candidates = [c for c in candidates if c["id"] != "InDesign.Application" or os.path.normcase(c["path"]) not in versioned_paths]
    return candidates, running, warnings


def mac_inventory(roots: list[Path] | None = None) -> tuple[list[dict], list[dict], list[str]]:
    roots = roots if roots is not None else [Path("/Applications"), Path.home() / "Applications"]
    candidates = []
    for root in roots:
        bundles = list(root.glob("*InDesign*.app")) + list(root.glob("*InDesign*/*InDesign*.app"))
        for bundle in bundles:
            if "server" in bundle.name.lower():
                continue
            try:
                info = plistlib.loads((bundle / "Contents/Info.plist").read_bytes())
                if "indesign" not in info.get("CFBundleIdentifier", "").lower():
                    continue
                path = str(bundle.resolve())
                executable = info.get("CFBundleExecutable")
                if not executable:
                    continue
                candidates.append({"id": path, "path": path, "executable": str(bundle.resolve() / "Contents/MacOS" / executable), "version_hint": info.get("CFBundleShortVersionString", ""), "backend": "macos-applescript"})
            except (OSError, plistlib.InvalidFileException):
                continue
    result = execute(["ps", "-ax", "-o", "pid=,comm="], timeout=10)
    if result.returncode:
        raise RuntimeFailure("Unable to enumerate macOS processes.")
    running = []
    for line in result.stdout.splitlines():
        match = re.match(r"\s*(\d+)\s+(.+)", line)
        if match:
            for candidate in candidates:
                if os.path.normcase(str(Path(match.group(2)).resolve())) == os.path.normcase(candidate["executable"]):
                    running.append({"pid": int(match.group(1)), "path": candidate["path"]})
    return list({c["id"]: c for c in candidates}.values()), running, []


def detect() -> dict:
    system = platform.system()
    warnings = []
    candidates, running = [], []
    try:
        if system == "Windows":
            candidates, running, warnings = windows_inventory()
        elif system == "Darwin":
            candidates, running, warnings = mac_inventory()
    except (OSError, ValueError, subprocess.TimeoutExpired, RuntimeFailure) as exc:
        warnings.append(str(exc))
    for candidate in candidates:
        candidate["running_pids"] = [p["pid"] for p in running if p.get("path") and os.path.normcase(str(Path(p["path"]).resolve())) == os.path.normcase(candidate["path"])]
    return {"system": system, "python": platform.python_version(), "native_platform": system in ("Windows", "Darwin"), "candidates": candidates, "running": running, "discovery_complete": not warnings, "warnings": warnings, "fallback": "Static validation and JSX handoff to a licensed Windows/macOS InDesign host; never claim Linux native layout."}


def select_target(inventory: dict, target: str | None, allow_launch: bool) -> dict:
    if not inventory["discovery_complete"]:
        raise RuntimeFailure("Discovery is incomplete: " + "; ".join(inventory["warnings"]))
    candidates = inventory["candidates"]
    if target:
        candidates = [c for c in candidates if c["id"] == target or os.path.normcase(c["path"]) == os.path.normcase(target)]
        if len(candidates) != 1:
            raise RuntimeFailure("Explicit target does not identify one discovered InDesign installation.")
    else:
        active = [c for c in candidates if c["running_pids"]]
        paths = {os.path.normcase(c["path"]) for c in active}
        if len(paths) > 1:
            raise RuntimeFailure("Multiple InDesign versions are running; specify --target from detect.")
        if active:
            candidates = active
        elif not allow_launch:
            raise RuntimeFailure("No running InDesign detected. Open the intended host or explicitly use --allow-launch.")
    if not candidates:
        raise RuntimeFailure("No usable InDesign installation detected. Use static checks/manual handoff.")
    candidate = max(candidates, key=lambda c: tuple(int(n) for n in re.findall(r"\d+", c["version_hint"])))
    if len(candidate["running_pids"]) > 1:
        raise RuntimeFailure("Multiple instances of the selected installation are running; do not guess a document owner.")
    if not candidate["running_pids"] and not allow_launch:
        raise RuntimeFailure("Selected InDesign is not running; launch was not allowed.")
    return candidate


def apple_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\n", "\\n") + '"'


def apple_script(request: dict) -> str:
    app = apple_string(request["target"]["path"])
    guard = "" if request["allow_launch"] else f'if not (application {app} is running) then error "Selected InDesign is no longer running"\n'
    return guard + f'''tell application {app}
set actualVersion to version as text
set actualPath to do script "app.fullName.fsName" language javascript
if actualPath does not start with {apple_string(request['target']['path'])} then error "Host identity mismatch"
set currentHash to do shell script ("/usr/bin/shasum -a 256 " & quoted form of {apple_string(request['script'])})
if currentHash does not start with {apple_string(request['script_sha256'])} then error "Script changed before dispatch"
set nativeResult to do script (POSIX file {apple_string(request['script'])}) language javascript
return actualVersion & linefeed & actualPath & linefeed & (nativeResult as text)
end tell
'''


def state_root() -> Path:
    root = Path(os.environ.get("INDESIGN_SKILL_STATE_DIR", str(Path(tempfile.gettempdir()) / "indesign-publication-production")))
    root.mkdir(parents=True, exist_ok=True)
    return root


def release_lock(lock: Path, job_id: str) -> None:
    if lock.exists() and read_json(lock).get("job_id") == job_id:
        lock.unlink()


def worker(job: Path) -> None:
    request = read_json(job / "request.json")
    receipt = read_json(job / "status.json")
    receipt.update(state="RUNNING", worker_pid=os.getpid(), stage="host-execution")
    atomic_json(job / "status.json", receipt)
    try:
        if file_hash(Path(request["script"])) != request["script_sha256"]:
            raise RuntimeFailure("Script changed after submission; no dispatch.")
        # The lock serializes this runner, not arbitrary third-party automation.
        target = select_target(detect(), request["target"]["id"], request["allow_launch"])
        if target["path"] != request["target"]["path"]:
            raise RuntimeFailure("Host registration changed after submission.")
        if file_hash(Path(request["script"])) != request["script_sha256"]:
            raise RuntimeFailure("Script changed during host discovery; no dispatch.")
        if target["backend"] == "windows-com":
            command = [powershell(), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "indesign_windows.ps1"), "-Request", str(job / "request.json")]
            result = execute(command)
            (job / "host.stdout.txt").write_text(result.stdout, encoding="utf-8")
            (job / "host.stderr.txt").write_text(result.stderr, encoding="utf-8")
            if result.returncode:
                raise RuntimeFailure(result.stderr.strip() or "COM bridge failed; inspect host logs.")
            host = json.loads(result.stdout)
        else:
            result = execute(["/usr/bin/osascript", "-"], input=apple_script(request))
            (job / "host.stdout.txt").write_text(result.stdout, encoding="utf-8")
            (job / "host.stderr.txt").write_text(result.stderr, encoding="utf-8")
            if result.returncode:
                raise RuntimeFailure(result.stderr.strip() or "Apple Events failed; check Automation permissions.")
            parts = result.stdout.strip().split("\n", 2)
            if len(parts) != 3:
                raise RuntimeFailure("AppleScript bridge returned an incomplete host result.")
            host = {"version": parts[0], "path": parts[1], "native_result": parts[2]}
        if request.get("expect_prefix") and not host["native_result"].startswith(request["expect_prefix"]):
            raise RuntimeFailure("Native result did not satisfy the requested prefix: " + host["native_result"])
        receipt.update(state="COMPLETED", stage="host-returned", host=host)
    except Exception as exc:
        receipt.update(state="FAILED", stage="host-error", error=str(exc))
    finally:
        receipt["finished_unix"] = time.time()
        atomic_json(job / "status.json", receipt)
        release_lock(Path(request["lock"]), receipt["job_id"])


def submit(script: Path, jobs: Path, target: str | None, allow_launch: bool, prefix: str | None) -> Path:
    script = script.resolve(strict=True)
    if script.suffix.lower() != ".jsx" or not script.read_bytes().startswith(b"\xef\xbb\xbf"):
        raise RuntimeFailure("Use a UTF-8 BOM .jsx file; no build was dispatched.")
    selected = select_target(detect(), target, allow_launch)
    jobs = jobs.resolve()
    jobs.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex
    job = jobs / job_id
    lock = state_root() / "host.lock.json"
    try:
        with lock.open("x", encoding="utf-8") as stream:
            json.dump({"job_id": job_id, "job": str(job), "submitted_unix": time.time()}, stream)
    except FileExistsError:
        raise RuntimeFailure("An existing run owns the host lock. Inspect/resume it; do not remove automatically: " + str(lock))
    try:
        job.mkdir()
        request = {"job_id": job_id, "script": str(script), "script_sha256": file_hash(script), "target": selected, "allow_launch": allow_launch, "expect_prefix": prefix, "lock": str(lock)}
        atomic_json(job / "request.json", request)
        atomic_json(job / "status.json", {"job_id": job_id, "job": str(job), "state": "QUEUED", "stage": "worker-start", "submitted_unix": time.time(), "script_sha256": request["script_sha256"]})
        with (job / "worker.log").open("wb") as log:
            options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "_worker", str(job)], stdin=subprocess.DEVNULL, stdout=log, stderr=log, **options)
    except Exception:
        release_lock(lock, job_id)
        raise
    return job


def wait_status(job: Path, seconds: float) -> dict:
    deadline = time.monotonic() + seconds
    while True:
        status = read_json(job / "status.json")
        if status["state"] in TERMINAL or time.monotonic() >= deadline:
            return status
        time.sleep(min(0.25, max(0, deadline - time.monotonic())))


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("detect", help="Read-only discovery; no COM activation or launch")
    run = sub.add_parser("run", help="Submit one authorized JSX; timeout returns its persistent job")
    run.add_argument("script", type=Path)
    run.add_argument("--jobs", type=Path, default=Path(".artifacts/indesign-runtime"))
    run.add_argument("--target", help="Discovered ProgID or macOS .app path")
    run.add_argument("--allow-launch", action="store_true", help="Opt in to launching an installed host")
    run.add_argument("--expect-prefix", help="Optional native result contract; COMPLETED alone is not publication acceptance")
    run.add_argument("--wait-seconds", type=float, default=10)
    status = sub.add_parser("status", help="Resume observation; never dispatch")
    status.add_argument("job", type=Path)
    status.add_argument("--wait-seconds", type=float, default=0)
    internal = sub.add_parser("_worker", help=argparse.SUPPRESS)
    internal.add_argument("job", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "detect":
            output = detect()
        elif args.action == "_worker":
            worker(args.job)
            return 0
        else:
            if not 0 <= args.wait_seconds <= 60:
                raise RuntimeFailure("--wait-seconds must be between 0 and 60; resume the same job for longer work.")
            job = submit(args.script, args.jobs, args.target, args.allow_launch, args.expect_prefix) if args.action == "run" else args.job
            output = wait_status(job, args.wait_seconds)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 1 if output.get("state") == "FAILED" else 0
    except (OSError, ValueError, RuntimeFailure) as exc:
        print(json.dumps({"state": "FAILED", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
