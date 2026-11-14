"""Portable resource-report contracts; no hardware needed."""
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from evolve.diagnostics import collect, assess, vulkan
from evolve.cli import main

G = 1024**3


class ResourceTests(unittest.TestCase):
    def test_project_local_vulkan_executable_is_not_executed(self):
        from evolve.diagnostics import windows
        with patch.object(windows.sys, 'platform', 'win32'), patch.object(windows.shutil, 'which', return_value=str(Path.cwd()/'vulkaninfo.exe')), patch.object(windows, 'system_directory', return_value=Path('C:/Windows/System32')):
            self.assertIsNone(windows.vulkan_tool())

    def test_excessive_probe_output_is_stopped(self):
        from evolve.diagnostics import windows
        with patch.object(windows.subprocess, 'Popen') as runner:
            runner.return_value.stdout = io.BytesIO(b'x'*300000)
            runner.return_value.wait.return_value = 0
            with self.assertRaises(OSError):
                windows.run(['tool'])
            runner.return_value.kill.assert_called_once()

    def test_probe_timeout_is_redacted(self):
        from evolve.diagnostics import windows
        import subprocess
        with patch.object(windows.subprocess, 'Popen') as runner:
            runner.return_value.stdout = io.BytesIO(b'')
            runner.return_value.wait.side_effect = [subprocess.TimeoutExpired('SECRET', 10), 0]
            with self.assertRaisesRegex(OSError, '^probe_timeout$'):
                windows.run(['tool'])

    def test_vulkan_fields_stay_with_their_device(self):
        text = 'GPU0:\n apiVersion = 1.4.1\n deviceType = DISCRETE\n deviceName = A\nGPU1:\n apiVersion = 1.3.2\n deviceType = INTEGRATED\n deviceName = B\n'
        with patch('evolve.diagnostics.windows.loader_present', return_value=True), patch('evolve.diagnostics.windows.vulkan_tool', return_value='tool'), patch('evolve.diagnostics.windows.run', return_value=text):
            devices = vulkan()['devices']
        self.assertEqual(devices[0]['apiVersion'], '1.4.1')
        self.assertEqual(devices[0]['deviceType'], 'DISCRETE')
        self.assertEqual(devices[1]['apiVersion'], '1.3.2')

    def test_successful_snapshot_and_privacy(self):
        with patch('evolve.diagnostics.windows.snapshot', return_value={
            'cpu': {'name': 'CPU', 'physical_cores': 8, 'logical_cores': 16},
            'ram': {'total_bytes': 32*G, 'available_bytes': 20*G},
            'gpus': [{'name': 'GPU', 'vram_bytes': 12*G}],
        }), patch('evolve.diagnostics.shutil.disk_usage', return_value=(100*G, 20*G, 80*G)), patch('evolve.diagnostics.vulkan', return_value={'state':'not_detected'}):
            result = collect(Path('.'))
        self.assertEqual(result['cpu']['physical_cores'], 8)
        self.assertEqual(result['storage']['free_bytes'], 80*G)
        self.assertNotIn(str(Path.cwd()), json.dumps(result))
        self.assertFalse(result['inference_tested'])

    def test_missing_system_information_does_not_crash(self):
        with patch('evolve.diagnostics.windows.snapshot', side_effect=OSError('PRIVATE_SECRET')), patch('evolve.diagnostics.shutil.disk_usage', side_effect=OSError('PRIVATE_SECRET')), patch('evolve.diagnostics.vulkan', side_effect=OSError('PRIVATE_SECRET')):
            result = collect(Path('.'))
        self.assertNotIn('PRIVATE_SECRET', json.dumps(result))
        self.assertTrue(result['warnings'])
        self.assertIsNone(result['storage']['free_bytes'])

    def test_unknown_gpu(self):
        result = assess({'available_bytes': 20*G}, [], {'free_bytes': 80*G})
        self.assertEqual(result['gpu_capacity'], 'unknown')
        self.assertEqual(result['compatibility'], 'untested')

    def test_low_disk(self):
        result = assess({'available_bytes': 20*G}, [], {'free_bytes': G})
        self.assertEqual(result['disk_budget_bytes'], 0)
        self.assertIn('low_disk', result['warnings'])

    def test_no_vulkan(self):
        with patch('evolve.diagnostics.windows.loader_present', return_value=False), patch('evolve.diagnostics.windows.vulkan_tool', return_value=None):
            self.assertEqual(vulkan()['state'], 'not_detected')

    def test_vulkan_loader_only(self):
        with patch('evolve.diagnostics.windows.loader_present', return_value=True), patch('evolve.diagnostics.windows.vulkan_tool', return_value=None):
            self.assertEqual(vulkan()['state'], 'detected_unverified')

    def test_vulkan_error_does_not_echo_output(self):
        with patch('evolve.diagnostics.windows.loader_present', return_value=True), patch('evolve.diagnostics.windows.vulkan_tool', return_value='vulkaninfo'), patch('evolve.diagnostics.windows.run', side_effect=OSError('SECRET')):
            result = vulkan()
        self.assertEqual(result['state'], 'error')
        self.assertNotIn('SECRET', json.dumps(result))

    def test_vulkan_summary_only_allowlisted_fields(self):
        text = 'deviceName = GPU\napiVersion = 1.3.0\nUSERNAME = SECRET\n'
        with patch('evolve.diagnostics.windows.loader_present', return_value=True), patch('evolve.diagnostics.windows.vulkan_tool', return_value='vulkaninfo'), patch('evolve.diagnostics.windows.run', return_value=text):
            result = vulkan()
        self.assertEqual(result['state'], 'working')
        self.assertNotIn('SECRET', json.dumps(result))

    def test_success_without_device_is_unverified(self):
        with patch('evolve.diagnostics.windows.loader_present', return_value=True), patch('evolve.diagnostics.windows.vulkan_tool', return_value='vulkaninfo'), patch('evolve.diagnostics.windows.run', return_value='nothing'):
            self.assertEqual(vulkan()['state'], 'detected_unverified')

    def test_json_cli_no_private_foundation_header(self):
        with patch('evolve.diagnostics.collect', return_value={'schema_version':1}), contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(main(['doctor','--resources','--json']), 0)
        self.assertEqual(json.loads(stream.getvalue()), {'schema_version':1})

    def test_runner_is_bounded_no_shell_or_network(self):
        from evolve.diagnostics import windows
        with patch('evolve.diagnostics.windows.subprocess.Popen') as runner:
            runner.return_value.wait.return_value = 0
            runner.return_value.stdout = io.BytesIO(b'ok')
            self.assertEqual(windows.run(['tool', '--summary']), 'ok')
        self.assertFalse(runner.call_args.kwargs['shell'])
        runner.return_value.wait.assert_called_once_with(timeout=10)

    def test_no_external_actions_with_hardware_probes_mocked(self):
        import sys
        events = []
        def audit(event, args):
            if active[0] and (event.startswith(('socket.', 'subprocess.')) or event in ('os.system','os.mkdir','os.remove','os.rename','winreg.SetValue','winreg.SetValueEx')):
                events.append(event)
                raise AssertionError(event)
        active = [False]
        sys.addaudithook(audit)
        with patch('evolve.diagnostics.windows.snapshot', return_value={}), patch('evolve.diagnostics.vulkan', return_value={'state':'not_detected'}):
            try:
                active[0] = True
                collect(Path('.'))
            finally:
                active[0] = False
        self.assertEqual(events, [])
