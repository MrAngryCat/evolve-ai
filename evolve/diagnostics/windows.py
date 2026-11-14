"""Read-only Windows probes. No command accepts model/user-authored code."""
import ctypes as C
import json
from pathlib import Path
import subprocess
import shutil
import threading
import sys
import uuid


def run(argv: list[str]) -> str:
    process = subprocess.Popen(argv, shell=False, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    chunks = []
    overflow = []
    def read():
        size = 0
        while chunk := process.stdout.read(16384):
            size += len(chunk)
            if size > 262144:
                overflow.append(True)
                process.kill()
                break
            chunks.append(chunk)
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        code = process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)
        raise OSError('probe_timeout') from None
    finally:
        reader.join(timeout=2)
        if not reader.is_alive():
            process.stdout.close()
    if code or overflow or reader.is_alive():
        raise OSError('probe_failed')
    return b''.join(chunks).decode('utf-8', errors='replace')


def vulkan_tool() -> str | None:
    """Execute only a known installation location, never project/CWD scripts."""
    if sys.platform != 'win32':
        return None
    candidate = shutil.which('vulkaninfo.exe')
    if not candidate:
        return None
    path = Path(candidate).resolve()
    roots = (system_directory().resolve(), Path('C:/VulkanSDK').resolve())
    if path.suffix.lower() == '.exe' and any(path.is_relative_to(root) for root in roots):
        return str(path)
    return None


def system_directory() -> Path:
    buffer = C.create_unicode_buffer(32768)
    size = C.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
    if not size or size >= len(buffer):
        raise OSError('system_directory_unavailable')
    return Path(buffer.value)


def loader_present() -> bool:
    return sys.platform == 'win32' and (system_directory() / 'vulkan-1.dll').is_file()


def memory() -> dict:
    class Memory(C.Structure):
        _fields_ = [('length', C.c_uint32), ('load', C.c_uint32)] + [
            (x, C.c_uint64) for x in ('total', 'available', 'page_total',
                                      'page_free', 'virtual', 'virtual_free', 'extended')]
    value = Memory()
    value.length = C.sizeof(value)
    if not C.windll.kernel32.GlobalMemoryStatusEx(C.byref(value)):
        raise OSError('memory_unavailable')
    return {'total_bytes': value.total, 'available_bytes': value.available,
            'used_bytes': value.total-value.available, 'load_percent': value.load,
            'source': 'GlobalMemoryStatusEx'}


def native_cpu() -> dict:
    import os
    import winreg
    result = {'logical_cores': os.cpu_count(), 'physical_cores': None,
              'load_percent': None, 'source': 'native topology / hardware registry (read-only)'}
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
        result['name'] = winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()[:160]
    class Info(C.Structure):
        _fields_ = [('mask', C.c_size_t), ('relationship', C.c_uint32), ('data', C.c_uint64*2)]
    size = C.c_uint32()
    fn = C.windll.kernel32.GetLogicalProcessorInformation
    fn(None, C.byref(size))
    if 0 < size.value < 1024*1024:
        buffer = C.create_string_buffer(size.value)
        if fn(buffer, C.byref(size)):
            entries = (Info*(size.value//C.sizeof(Info))).from_buffer_copy(buffer)
            result['physical_cores'] = sum(e.relationship == 0 for e in entries) or None
    return result


def adapters() -> list[dict]:
    """DXGI dedicated bytes (SIZE_T), avoiding 32-bit WMI AdapterRAM overflow."""
    class Desc(C.Structure):
        _fields_ = [('description', C.c_wchar*128), ('vendor', C.c_uint32),
                    ('device', C.c_uint32), ('subsystem', C.c_uint32),
                    ('revision', C.c_uint32), ('dedicated', C.c_size_t),
                    ('system', C.c_size_t), ('shared', C.c_size_t),
                    ('luid_low', C.c_uint32), ('luid_high', C.c_int32),
                    ('flags', C.c_uint32)]

    def call(obj, slot, restype, argtypes, *args):
        table = C.cast(obj, C.POINTER(C.POINTER(C.c_void_p))).contents
        return C.WINFUNCTYPE(restype, C.c_void_p, *argtypes)(table[slot])(obj, *args)

    dxgi = C.WinDLL('dxgi.dll', winmode=0x800)
    factory = C.c_void_p()
    iid = (C.c_ubyte*16).from_buffer_copy(uuid.UUID('770aae78-f26f-4dba-a829-253c83d1b387').bytes_le)
    create = dxgi.CreateDXGIFactory1
    create.argtypes = [C.c_void_p, C.POINTER(C.c_void_p)]
    create.restype = C.c_int32
    if create(C.byref(iid), C.byref(factory)) < 0:
        raise OSError('dxgi_unavailable')
    output = []
    try:
        for index in range(16):
            adapter = C.c_void_p()
            hr = call(factory, 12, C.c_int32, [C.c_uint, C.POINTER(C.c_void_p)], index, C.byref(adapter))
            if hr == -2005270526:  # DXGI_ERROR_NOT_FOUND
                break
            if hr < 0:
                raise OSError('dxgi_enumeration_failed')
            try:
                desc = Desc()
                if call(adapter, 10, C.c_int32, [C.c_void_p], C.byref(desc)) < 0:
                    raise OSError('dxgi_description_failed')
                if not desc.flags & 2:  # exclude software adapters
                    output.append({'name': desc.description, 'vram_bytes': desc.dedicated,
                                   'shared_limit_bytes': desc.shared, 'source': 'DXGI',
                                   'inference_tested': False})
            finally:
                call(adapter, 2, C.c_ulong, [])
    finally:
        call(factory, 2, C.c_ulong, [])
    return output


# Fixed property projection excludes usernames, computer names, IDs and serials.
CIM_SCRIPT = r'''
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$ErrorActionPreference='Stop'
$cpu=@(); $drivers=@(); $os=@()
try {$cpu=@(Get-CimInstance -ClassName Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,Architecture,LoadPercentage)} catch {}
try {$drivers=@(Get-CimInstance -ClassName Win32_VideoController | Select-Object Name,DriverVersion)} catch {}
try {$os=@(Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object OSArchitecture)} catch {}
@{cpu=$cpu;drivers=$drivers;os=$os} | ConvertTo-Json -Depth 4 -Compress
'''


def snapshot() -> dict:
    if sys.platform != 'win32':
        return {'warnings': ['windows_probes_unavailable']}
    result = {'warnings': []}
    for key, probe in [('ram', memory), ('gpus', adapters)]:
        try:
            result[key] = probe()
        except (OSError, ValueError, AttributeError):
            result['warnings'].append(key+'_unavailable')
    data = {}
    try:
        ps = system_directory() / 'WindowsPowerShell/v1.0/powershell.exe'
        data = json.loads(run([str(ps), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', CIM_SCRIPT]))
    except (OSError, ValueError, subprocess.SubprocessError):
        result['warnings'].append('cim_unavailable')
    cpus = data.get('cpu', [])
    if cpus:
        result['cpu'] = {'name': str(cpus[0].get('Name', 'unknown'))[:160],
                         'physical_cores': sum(x.get('NumberOfCores') or 0 for x in cpus) or None,
                         'logical_cores': sum(x.get('NumberOfLogicalProcessors') or 0 for x in cpus) or None,
                         'architecture_code': cpus[0].get('Architecture'),
                         'load_percent': cpus[0].get('LoadPercentage'),
                         'source': 'local CIM; load is provider sample, not benchmark'}
    else:
        result['warnings'].append('cim_cpu_unavailable')
        try:
            result['cpu'] = native_cpu()
        except (OSError, AttributeError):
            pass
    drivers = {x.get('Name'): x.get('DriverVersion') for x in data.get('drivers', [])}
    for gpu in result.get('gpus', []):
        gpu['driver_version'] = drivers.get(gpu['name'])
    version = sys.getwindowsversion()
    result['os'] = {'name': 'Windows', 'kernel': f'{version.major}.{version.minor}',
                    'build': version.build,
                    'architecture': (data.get('os') or [{}])[0].get('OSArchitecture')}
    native = C.create_string_buffer(64)
    C.windll.kernel32.GetNativeSystemInfo(native)
    arch = {0:'x86', 9:'x64', 12:'ARM64'}.get(C.c_uint16.from_buffer(native).value, 'unknown')
    result['os']['architecture'] = result['os']['architecture'] or arch
    result.setdefault('cpu', {})['architecture'] = arch
    return result
