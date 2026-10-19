"""Temporary text fixtures and harmless hello/Get-Date process checks only."""
import base64
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "plugin" / "owner_operations.py"
SPEC = importlib.util.spec_from_file_location("tested_owner_operations", MODULE_PATH)
operations_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = operations_module
SPEC.loader.exec_module(operations_module)
OwnerOperations = operations_module.OwnerOperations


class OwnerOperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.ops = OwnerOperations(self.workspace)

    def tearDown(self):
        self.temp.cleanup()

    def test_constructor_does_not_create_directories_or_claim_authorization(self):
        self.assertFalse(self.workspace.exists())
        self.assertFalse(hasattr(self.ops, "owner_id"))

    def test_write_read_unicode_and_line_endings_without_shell_interpretation(self):
        target = self.root / "elsewhere" / "notes [one] $literal's.txt"
        text = "hello，三月七\r\nsecond line\n"
        written = self.ops.write_text(target, text)
        self.assertTrue(written["ok"])
        self.assertEqual(written["characters_written"], len(text))
        self.assertEqual(written["size_bytes"], len(text.encode("utf-8")))
        result = self.ops.read_text(target)
        self.assertEqual(result["text"], text)
        self.assertFalse(result["truncated"])
        self.assertEqual(Path(result["path"]), target)

    def test_absolute_paths_outside_workspace_have_no_directory_allowlist(self):
        outside = self.root / "outside-workspace.txt"
        self.ops.write_text(outside, "hello")
        self.assertEqual(self.ops.read_text(outside)["text"], "hello")
        self.assertFalse(self.workspace.exists())

    def test_append_and_overwrite_are_explicit(self):
        target = self.root / "append.txt"
        self.ops.write_text(target, "first\n")
        self.ops.write_text(target, "hello\n", append=True)
        self.assertEqual(self.ops.read_text(target)["text"], "first\nhello\n")
        self.ops.write_text(target, "replacement")
        self.assertEqual(self.ops.read_text(target)["text"], "replacement")

    def test_read_limits_characters_without_splitting_unicode(self):
        target = self.root / "bounded.txt"
        self.ops.write_text(target, "三月七hello")
        result = self.ops.read_text(target, max_chars=3)
        self.assertEqual(result["text"], "三月七")
        self.assertTrue(result["truncated"])
        self.assertEqual(result["limit_chars"], 3)

    def test_read_exact_limit_does_not_claim_truncation(self):
        target = self.root / "exact.txt"
        self.ops.write_text(target, "hello")
        self.assertFalse(self.ops.read_text(target, max_chars=5)["truncated"])

    def test_explicit_encoding_is_supported(self):
        target = self.root / "utf16.txt"
        self.ops.write_text(target, "hello三月", encoding="utf-16")
        self.assertEqual(self.ops.read_text(target, encoding="utf-16")["text"], "hello三月")

    def test_listing_is_bounded_and_preserves_entry_types(self):
        self.ops.write_text(self.root / "a.txt", "hello")
        (self.root / "folder").mkdir()
        listing = self.ops.list_dir(self.root)
        self.assertEqual({item["type"] for item in listing["entries"]}, {"file", "directory"})
        self.assertFalse(listing["truncated"])
        self.assertTrue(all(Path(item["path"]).is_absolute() for item in listing["entries"]))
        limited = self.ops.list_dir(self.root, limit=1)
        self.assertEqual(len(limited["entries"]), 1)
        self.assertTrue(limited["truncated"])

    def test_relative_paths_are_rejected_before_any_write(self):
        for action in (lambda: self.ops.read_text("relative.txt"),
                       lambda: self.ops.list_dir("relative"),
                       lambda: self.ops.write_text("relative.txt", "hello"),
                       lambda: self.ops.run_command("Write-Output 'hello'", cwd="relative")):
            with self.assertRaisesRegex(ValueError, "absolute"):
                action()

    def test_missing_paths_and_file_directory_mismatches_raise(self):
        with self.assertRaises(FileNotFoundError):
            self.ops.read_text(self.root / "missing.txt")
        target = self.root / "text.txt"
        self.ops.write_text(target, "hello")
        with self.assertRaises(NotADirectoryError):
            self.ops.list_dir(target)
        with self.assertRaises(NotADirectoryError):
            self.ops.run_command("Write-Output 'hello'", cwd=target)

    def test_invalid_limits_and_nonliteral_write_values_are_rejected(self):
        for limit in (0, -1, True, 1.5, self.ops.max_read_chars + 1):
            with self.assertRaises(ValueError):
                self.ops.read_text(self.root / "absent", max_chars=limit)
        with self.assertRaises(TypeError):
            self.ops.write_text(self.root / "text.txt", ["hello"])
        with self.assertRaises(TypeError):
            self.ops.write_text(self.root / "text.txt", "hello", append="yes")
        for timeout in (0, -1, float("inf"), float("nan"), True, 121):
            with self.assertRaises(ValueError):
                self.ops.run_command("Write-Output 'hello'", timeout=timeout)

    def test_invalid_constructor_bounds_are_rejected(self):
        for config in ({"max_output_chars": 0}, {"max_read_chars": False}, {"max_list_entries": 0},
                       {"default_timeout": 121}, {"max_timeout": float("inf")}):
            with self.assertRaises(ValueError):
                OwnerOperations(self.workspace, **config)

    def _fake_process(self, code=0):
        process = mock.Mock()
        process.returncode = code
        process.poll.side_effect = lambda: process.returncode
        process.stdout = mock.Mock()
        return process

    def test_run_uses_encoded_argv_profile_free_noninteractive_and_hidden_start(self):
        process = self._fake_process()
        command = "Write-Output 'hello'; Get-Date -Format yyyy-MM-dd"
        with mock.patch.object(operations_module.subprocess, "Popen", return_value=process) as popen, \
             mock.patch.object(self.ops, "_powershell", return_value="powershell.exe"), \
             mock.patch.object(self.ops, "_read_available", side_effect=[(b"hello", False), (b"", True)]):
            result = self.ops.run_command(command)
        args, kwargs = popen.call_args
        argv = args[0]
        self.assertIn("-NoProfile", argv)
        self.assertIn("-NonInteractive", argv)
        self.assertNotIn("-ExecutionPolicy", argv)
        self.assertNotIn("-Verb", argv)
        script = base64.b64decode(argv[-1]).decode("utf-16-le")
        self.assertTrue(script.endswith(command))
        self.assertIn("Start-Process:WindowStyle", script)
        self.assertIn("'Hidden'", script)
        self.assertNotIn("shell", kwargs)
        self.assertEqual(kwargs["cwd"], str(self.workspace))
        self.assertEqual(kwargs["stdin"], operations_module.subprocess.DEVNULL)
        if os.name == "nt":
            self.assertTrue(kwargs["creationflags"] & operations_module.subprocess.CREATE_NO_WINDOW)
            self.assertEqual(kwargs["startupinfo"].wShowWindow, operations_module.subprocess.SW_HIDE)
        self.assertEqual(result["text"], "hello")
        self.assertTrue(result["ok"])

    def test_run_output_is_bounded_but_remaining_pipe_is_drained(self):
        process = self._fake_process()
        with mock.patch.object(operations_module.subprocess, "Popen", return_value=process), \
             mock.patch.object(self.ops, "_powershell", return_value="powershell.exe"), \
             mock.patch.object(self.ops, "_read_available", side_effect=[(b"hello" * 5000, False), (b"more", False), (b"", True)]) as drain:
            result = self.ops.run_command("Write-Output 'hello'", max_output_chars=7)
        self.assertEqual(result["text"], "hellohe")
        self.assertTrue(result["truncated"])
        self.assertEqual(drain.call_count, 3)
        process.stdout.close.assert_called_once()

    def test_run_keeps_explicit_cwd_and_reports_nonzero_exit(self):
        process = self._fake_process(code=3)
        with mock.patch.object(operations_module.subprocess, "Popen", return_value=process) as popen, \
             mock.patch.object(self.ops, "_powershell", return_value="powershell.exe"), \
             mock.patch.object(self.ops, "_read_available", return_value=(b"", True)):
            result = self.ops.run_command("Write-Output 'hello'", cwd=self.root)
        self.assertEqual(popen.call_args.kwargs["cwd"], str(self.root))
        self.assertEqual(result["exit_code"], 3)
        self.assertFalse(result["ok"])
        self.assertFalse(self.workspace.exists())

    def test_timeout_terminates_only_the_created_process_and_is_reported(self):
        process = self._fake_process(code=None)

        def terminate(value):
            self.assertIs(value, process)
            process.returncode = -9

        with mock.patch.object(operations_module.subprocess, "Popen", return_value=process), \
             mock.patch.object(self.ops, "_powershell", return_value="powershell.exe"), \
             mock.patch.object(self.ops, "_read_available", return_value=(b"", True)), \
             mock.patch.object(self.ops, "_terminate_tree", side_effect=terminate) as kill, \
             mock.patch.object(operations_module.time, "monotonic", side_effect=[0, .2, .21]):
            result = self.ops.run_command("Write-Output 'hello'", timeout=.1)
        kill.assert_called_once_with(process)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["exit_code"], -9)
        self.assertFalse(result["ok"])

    def test_read_failure_terminates_own_process_and_closes_pipe(self):
        process = self._fake_process(code=None)
        with mock.patch.object(operations_module.subprocess, "Popen", return_value=process), \
             mock.patch.object(self.ops, "_powershell", return_value="powershell.exe"), \
             mock.patch.object(self.ops, "_read_available", side_effect=OSError("test pipe")), \
             mock.patch.object(self.ops, "_terminate_tree") as kill:
            with self.assertRaises(OSError):
                self.ops.run_command("Write-Output 'hello'")
        kill.assert_called_once_with(process)
        process.stdout.close.assert_called_once()

    @unittest.skipUnless(os.name == "nt" and (shutil.which("powershell.exe") or shutil.which("pwsh.exe")), "Requires local Windows PowerShell")
    def test_real_harmless_hello_and_get_date(self):
        result = self.ops.run_command("Write-Output 'hello 三月七'; Get-Date -Format yyyy-MM-dd", timeout=15)
        self.assertTrue(result["ok"], result)
        self.assertFalse(result["timed_out"])
        self.assertIn("hello 三月七", result["text"])
        self.assertRegex(result["text"], r"\d{4}-\d{2}-\d{2}")

    @unittest.skipUnless(os.name == "nt" and (shutil.which("powershell.exe") or shutil.which("pwsh.exe")), "Requires local Windows PowerShell")
    def test_real_harmless_hello_output_limit(self):
        result = self.ops.run_command("Write-Output ('hello' * 2000)", timeout=15, max_output_chars=21)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["truncated"])
        self.assertEqual(len(result["text"]), 21)


if __name__ == "__main__":
    unittest.main()
