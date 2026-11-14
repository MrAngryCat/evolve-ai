"""Finite resource diagnostics, separate from any future agent/tool executor."""
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import struct
import sys

from . import windows

GIB = 1024**3


def vulkan() -> dict:
    loader = windows.loader_present()
    executable = windows.vulkan_tool()
    result = {'state': 'detected_unverified' if loader or executable else 'not_detected',
              'loader_present': loader, 'tool_present': bool(executable),
              'devices': [], 'inference_tested': False}
    if executable:
        try:
            text = windows.run([executable, '--summary'])
            # Never publish raw stdout/stderr: may contain paths, hostnames, IDs.
            current = None
            for line in text.splitlines():
                if re.fullmatch(r'\s*GPU\d+:\s*', line):
                    current = {}
                    result['devices'].append(current)
                match = re.fullmatch(r'\s*(deviceName|apiVersion|driverName|driverInfo|driverVersion|deviceType)\s*=\s*([^\r\n]{1,160})', line)
                if match:
                    if current is None:
                        current = {}
                        result['devices'].append(current)
                    current[match[1]] = ''.join(c for c in match[2] if c.isprintable())
            result['devices'] = [d for d in result['devices'] if d.get('deviceName')]
            if result['devices']:
                result['state'] = 'working'
        except Exception:
            result['state'] = 'error'
    return result


def assess(ram: dict, gpus: list, storage: dict) -> dict:
    """Conservative planning budgets, not measured model requirements."""
    available, free = ram.get('available_bytes'), storage.get('free_bytes')
    vram = max((x.get('vram_bytes') or 0 for x in gpus), default=0)
    result = {'compatibility': 'untested', 'gpu_capacity': 'known' if vram else 'unknown',
              'ram_budget_bytes': max(0, available-4*GIB) if available is not None else None,
              'disk_budget_bytes': max(0, free-20*GIB) if free is not None else None,
              'vram_budget_bytes': max(0, vram-2*GIB) if vram else None,
              'warnings': [], 'assumption': 'reserve 4 GiB available RAM, 2 GiB VRAM, 20 GiB disk; not enforced'}
    if free is not None and free < 30*GIB:
        result['warnings'].append('low_disk')
    if available is not None and available < 8*GIB:
        result['warnings'].append('low_available_ram')
    result['candidates'] = []
    for name, params in [('Qwen3.5-9B', 9), ('Qwen3.5-35B-A3B', 35)]:
        # Decimal parameters * 4 bits / 8. Actual checkpoint/quant metadata differs.
        lower = int(params*1e9/2)
        result['candidates'].append({'name': name, 'illustrative_4bit_weight_lower_bytes': lower,
            'ram_weights_only_fit': None if available is None else result['ram_budget_bytes'] >= lower,
            'vram_weights_only_fit': None if not vram else result['vram_budget_bytes'] >= lower,
            'disk_weights_only_fit': None if free is None else result['disk_budget_bytes'] >= lower,
            'verdict': 'preliminary_only; actual GGUF, runtime, KV cache and offload must be measured'})
    return result


def collect(project: Path) -> dict:
    report = {'schema_version': 1, 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
              'python': {'version': sys.version.split()[0], 'bits': struct.calcsize('P')*8},
              'os': {}, 'cpu': {}, 'ram': {}, 'gpus': [],
              'storage': {'free_bytes': None, 'total_bytes': None, 'medium': 'not_verified'},
              'warnings': [], 'inference_tested': False}
    try:
        report.update(windows.snapshot())
    except Exception:
        report['warnings'].append('system_information_unavailable')
    try:
        usage = shutil.disk_usage(project)
        report['storage'].update(total_bytes=usage[0], free_bytes=usage[2])
    except OSError:
        report['warnings'].append('storage_unavailable')
    try:
        report['vulkan'] = vulkan()
    except Exception:
        report['vulkan'] = {'state': 'error', 'inference_tested': False}
    report['tools'] = {name: bool(shutil.which(name)) for name in ('powershell', 'git', 'vulkaninfo')}
    report['planning'] = assess(report['ram'], report['gpus'], report['storage'])
    if not report['cpu']:
        report['warnings'].append('cpu_unknown')
    if not report['gpus']:
        report['warnings'].append('gpu_unknown')
    return report
