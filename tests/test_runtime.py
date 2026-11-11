from __future__ import annotations

import importlib.util
import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import indesign_runtime as runtime
import package_skill


def candidate(name="InDesign.Application.2026", running=True, version="2026"):
    return {"id": name, "path": name, "version_hint": version, "backend": "windows-com", "running_pids": [20] if running else []}


def inventory(*candidates):
    return {"discovery_complete": True, "warnings": [], "candidates": list(candidates)}


class RuntimeTests(unittest.TestCase):
    def test_localserver_parse_preserves_spaces_unicode_and_never_evaluates(self):
        self.assertEqual(runtime.windows_executable('"C:\\Adobe 中文\\InDesign.exe" /Automation'), 'C:\\Adobe 中文\\InDesign.exe')
        self.assertEqual(runtime.windows_executable('C:\\Adobe 2035\\InDesign.exe /Automation'), 'C:\\Adobe 2035\\InDesign.exe')
        self.assertEqual(runtime.windows_executable('echo injected'), '')

    def test_prefers_running_old_version_over_new_cold_version(self):
        old, new = candidate("old", version="19"), candidate("new", False, "22")
        self.assertEqual(runtime.select_target(inventory(old, new), None, False), old)

    def test_future_version_has_no_year_allowlist(self):
        old, new = candidate("old", False, "21"), candidate("future", False, "39.2")
        self.assertEqual(runtime.select_target(inventory(old, new), None, True), new)

    def test_multiple_running_versions_require_target(self):
        a, b = candidate("A"), candidate("B")
        with self.assertRaises(runtime.RuntimeFailure):
            runtime.select_target(inventory(a, b), None, True)
        self.assertEqual(runtime.select_target(inventory(a, b), "A", False), a)

    def test_multiple_instances_not_guessed(self):
        a = candidate();a["running_pids"] = [1, 2]
        with self.assertRaises(runtime.RuntimeFailure):
            runtime.select_target(inventory(a), a["id"], False)

    def test_explicit_cold_target_cannot_launch_implicitly(self):
        a = candidate(running=False)
        with self.assertRaises(runtime.RuntimeFailure):
            runtime.select_target(inventory(a), a["id"], False)

    def test_incomplete_discovery_cannot_run(self):
        with self.assertRaises(runtime.RuntimeFailure):
            runtime.select_target({"discovery_complete": False, "warnings": ["access denied"]}, None, True)

    def test_linux_degrades_without_com_or_applescript(self):
        with patch.object(runtime.platform, "system", return_value="Linux"), patch.object(runtime, "windows_inventory") as windows, patch.object(runtime, "mac_inventory") as mac:
            result = runtime.detect()
            self.assertFalse(result["native_platform"])
            self.assertEqual(result["candidates"], [])
            windows.assert_not_called();mac.assert_not_called()

    def test_macos_real_plist_fixture_and_running_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);bundle = root / "Adobe InDesign Future" / "Adobe InDesign Future.app"
            (bundle / "Contents").mkdir(parents=True)
            (bundle / "Contents/Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "com.adobe.InDesign", "CFBundleShortVersionString": "42.1", "CFBundleExecutable": "Adobe InDesign"}))
            executable = bundle / "Contents/MacOS/Adobe InDesign"
            helper = bundle / "Contents/MacOS/AdobeCrashDaemon"
            process = subprocess.CompletedProcess([], 0, f" 99 {executable}\n100 {helper}\n", "")
            with patch.object(runtime, "execute", return_value=process):
                candidates, running, warnings = runtime.mac_inventory([root])
            self.assertEqual(candidates[0]["version_hint"], "42.1")
            self.assertEqual(running[0]["path"], str(bundle.resolve()))
            self.assertEqual(len(running), 1)
            self.assertEqual(warnings, [])

    def test_applescript_escapes_paths_and_guards_cold_launch(self):
        request = {"target": {"path": '/Applications/A "quoted" InDesign.app'}, "script": '/tmp/中文 $`".jsx', "script_sha256": "123", "allow_launch": False}
        source = runtime.apple_script(request)
        self.assertIn('if not (application ', source)
        self.assertIn('\\"quoted\\"', source)
        self.assertIn('language javascript', source)

    def test_macos_running_bundle_through_symlinked_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);real=root / "real";real.mkdir();alias=root / "alias"
            try:alias.symlink_to(real,target_is_directory=True)
            except OSError:self.skipTest("OS account does not permit creating directory symlinks")
            bundle=alias / "Adobe InDesign.app";(bundle / "Contents").mkdir(parents=True)
            (bundle / "Contents/Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier":"com.adobe.InDesign","CFBundleShortVersionString":"42.1","CFBundleExecutable":"Adobe InDesign"}))
            process=subprocess.CompletedProcess([],0,f" 99 {bundle / 'Contents/MacOS/Adobe InDesign'}\n","")
            with patch.object(runtime,"execute",return_value=process):
                candidates,running,_=runtime.mac_inventory([alias])
            self.assertEqual(running,[{"pid":99,"path":str(bundle.resolve())}])

    def test_wait_returns_running_without_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp);runtime.atomic_json(job / "status.json", {"state": "RUNNING", "job_id": "same"})
            with patch.object(runtime, "submit") as submit:
                self.assertEqual(runtime.wait_status(job, 0)["job_id"], "same")
                submit.assert_not_called()

    def test_existing_host_lock_prevents_second_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);script = root / "sample.jsx";script.write_text("'PASS';", encoding="utf-8-sig")
            lock = root / "host.lock.json";lock.write_text('{"job_id":"original"}', encoding="utf-8")
            with patch.object(runtime, "state_root", return_value=root), patch.object(runtime, "detect", return_value=inventory(candidate())), patch.object(runtime.subprocess, "Popen") as popen:
                with self.assertRaises(runtime.RuntimeFailure):
                    runtime.submit(script, root / "jobs", None, False, None)
                popen.assert_not_called()
            self.assertEqual(json.loads(lock.read_text())["job_id"], "original")

    def test_bom_required_before_discovery_or_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "sample.jsx";script.write_text("bad", encoding="utf-8")
            with patch.object(runtime, "detect") as detect:
                with self.assertRaises(runtime.RuntimeFailure):
                    runtime.submit(script, Path(tmp), None, False, None)
                detect.assert_not_called()

    def test_lock_owned_by_other_job_is_not_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "lock.json";lock.write_text('{"job_id":"other"}')
            runtime.release_lock(lock, "ours")
            self.assertTrue(lock.exists())

    def test_worker_rejects_modified_script_and_records_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp);script = job / "script.jsx";script.write_text("changed")
            runtime.atomic_json(job / "request.json", {"script": str(script), "script_sha256": "incorrect", "lock": str(job / "lock")})
            runtime.atomic_json(job / "status.json", {"job_id": "test", "state": "QUEUED"})
            with patch.object(runtime, "detect") as detect:
                runtime.worker(job);detect.assert_not_called()
            self.assertEqual(runtime.read_json(job / "status.json")["state"], "FAILED")

    def test_package_omits_git_artifacts_caches_and_manuscripts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill";root.mkdir()
            for name in ("SKILL.md", "README.md", "LICENSE"):(root / name).write_text("public")
            for name in (".git/config", ".artifacts/request.json", "scripts/__pycache__/secret.json", "manuscripts/private.md", "scripts/tool.py"):
                p=root / name;p.parent.mkdir(parents=True, exist_ok=True);p.write_text("fixture")
            (root / "references").mkdir();(root / "references/personal-review.json").write_text("not public")
            (root / "distribution-files.json").write_text(json.dumps({"files": ["SKILL.md", "README.md", "LICENSE", "scripts/tool.py"]}))
            output = Path(tmp) / "skill.zip";package_skill.package(root, output)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {"SKILL.md", "README.md", "LICENSE", "scripts/tool.py"})

    def test_worker_rechecks_script_after_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp);script = job / "script.jsx";script.write_text("original")
            target = candidate()
            runtime.atomic_json(job / "request.json", {"script": str(script), "script_sha256": runtime.file_hash(script), "target": target, "allow_launch": False, "lock": str(job / "lock")})
            runtime.atomic_json(job / "status.json", {"job_id": "test", "state": "QUEUED"})
            def detect_and_mutate():
                script.write_text("replaced during discovery")
                return inventory(target)
            with patch.object(runtime, "detect", side_effect=detect_and_mutate), patch.object(runtime, "execute") as execute:
                runtime.worker(job);execute.assert_not_called()
            self.assertEqual(runtime.read_json(job / "status.json")["state"], "FAILED")

    def test_explicit_distribution_manifest_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root / "distribution-files.json").write_text(json.dumps({"files":["../private.md"]}))
            with self.assertRaises(ValueError):package_skill.public_files(root)

    def test_native_failure_prefix_is_not_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            job=Path(tmp);script=job / "script.jsx";script.write_text("original")
            target=candidate()
            runtime.atomic_json(job / "request.json", {"script":str(script),"script_sha256":runtime.file_hash(script),"target":target,"allow_launch":False,"expect_prefix":"PASS ","lock":str(job / "lock")})
            runtime.atomic_json(job / "status.json", {"job_id":"test","state":"QUEUED"})
            result=subprocess.CompletedProcess([],0,json.dumps({"version":"21","path":target['path'],"native_result":"FAIL overset"}),"")
            with patch.object(runtime,"detect",return_value=inventory(target)),patch.object(runtime,"execute",return_value=result),patch.object(runtime,"powershell",return_value="powershell.exe"):
                runtime.worker(job)
            self.assertEqual(runtime.read_json(job / "status.json")["state"],"FAILED")
            self.assertIn("FAIL overset",(job / "host.stdout.txt").read_text())

    def test_probe_is_bom_encoded(self):
        self.assertTrue((ROOT / "scripts/runtime_probe.jsx").read_bytes().startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()
