"""Offline acceptance tests for the foundation's public CLI."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / ".test-tmp"


class CliTests(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)

    def run_cli(self, *args, guarded=False):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)
        env["PYTHONIOENCODING"] = "utf-8"
        command = [sys.executable, "-B", "-m", "evolve", *args]
        if guarded:
            # Audit real operations, including during package import. A failure
            # aborts the real command; no fake backend replaces application code.
            script = '''
import os, runpy, sys
def guard(event, args):
    if event.startswith(("socket.", "subprocess.", "os.spawn", "os.exec")):
        raise RuntimeError("Forbidden operation: " + event)
    if event in {"os.system", "os.mkdir", "os.remove", "os.rename", "os.rmdir", "os.truncate", "os.chmod", "os.link", "os.symlink"}:
        raise RuntimeError("Forbidden operation: " + event)
    if event == "open":
        mode, flags = args[1], args[2]
        if (mode and any(c in mode for c in "wax+")) or (flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            raise RuntimeError("Forbidden file write")
sys.addaudithook(guard)
sys.argv = ["evolve", *sys.argv[1:]]
runpy.run_module("evolve", run_name="__main__")
'''
            command = [sys.executable, "-B", "-c", script, *args]
        return subprocess.run(command, cwd=self.cwd, env=env, capture_output=True,
                              text=True, encoding="utf-8", timeout=10, check=False)

    def config(self, content, name="evolve.toml"):
        path = self.cwd / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_help_and_empty_invocation(self):
        for args in [(), ("--help",), ("doctor", "--help"), ("status", "--help")]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)

    def test_status_reports_only_foundation_capabilities(self):
        result = self.run_cli("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in ["Evolve AI 0.0.0", "offline", "idle", "Models: none", "External APIs: disabled", "not implemented"]:
            self.assertIn(expected, result.stdout)

    def test_doctor_reports_environment_and_missing_default(self):
        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in ["OS:", "Python:", str(self.cwd), "defaults", "GPU/Vulkan: not checked"]:
            self.assertIn(expected, result.stdout)

    def test_tracked_configuration_is_usable(self):
        result = self.run_cli("--config", str(ROOT / "evolve.toml"), "doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(ROOT / "evolve.toml"), result.stdout)

    def test_mock_mode_does_not_claim_an_inference_backend(self):
        self.config('[evolve]\nmode = "mock"\n')
        result = self.run_cli("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in ["mock", "Models: none", "not implemented"]:
            self.assertIn(expected, result.stdout)

    def test_explicit_config_supports_spaces_and_cyrillic(self):
        path = self.config('[evolve]\nmode = "mock"\n', "конфиг evolve.toml")
        result = self.run_cli("--config", str(path), "status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mock", result.stdout)

    def test_explicit_missing_config_is_an_error(self):
        result = self.run_cli("--config", str(self.cwd / "absent.toml"), "doctor")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Ошибка конфигурации", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_config_is_rejected_without_echoing_contents(self):
        for content in ['[evolve', '[evolve]\nmode = "cloud"',
                        '[evolve]\nmode = 123', '[evolve]\nmode = []',
                        '[evolve]\nmode = true', '[evolve]\napi_key = "PRIVATE_SENTINEL"',
                        'secret = "PRIVATE_SENTINEL"', 'evolve = "PRIVATE_SENTINEL"',
                        '[evolve]\nmode = ' + '[' * 1500 + '0' + ']' * 1500,
                        '[evolve]\nmode = ' + '1' * 5000,
                        '# PRIVATE_SENTINEL\n' + 'x' * 17000]:
            with self.subTest(content=content[:40]):
                self.config(content)
                for name in ("doctor", "status"):
                    result = self.run_cli(name)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("Ошибка конфигурации", result.stderr)
                    self.assertNotIn("PRIVATE_SENTINEL", result.stdout + result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_non_utf8_config_is_a_clean_error(self):
        (self.cwd / "evolve.toml").write_bytes(b"\xff\xfe")
        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_config_directory_is_a_clean_error(self):
        (self.cwd / "evolve.toml").mkdir()
        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_help_does_not_need_valid_configuration(self):
        self.config("broken config")
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unknown_command_and_unexpected_arguments_fail(self):
        for args in [("run",), ("status", "extra"), ("--unknown",)]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)

    def test_commands_do_not_access_network_execute_processes_or_write_files(self):
        for mode in ("offline", "mock"):
            self.config(f'[evolve]\nmode = "{mode}"\n')
            before = {p.relative_to(self.cwd): p.read_bytes() for p in self.cwd.rglob("*") if p.is_file()}
            for name in ("--help", "doctor", "status"):
                with self.subTest(mode=mode, name=name):
                    result = self.run_cli(name, guarded=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
            after = {p.relative_to(self.cwd): p.read_bytes() for p in self.cwd.rglob("*") if p.is_file()}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
