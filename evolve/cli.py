"""Finite, read-only CLI commands for phase 00."""

import argparse
from pathlib import Path
import sys

from evolve import __version__
from evolve.config import ConfigError, load_config


def main(argv: list[str] | None = None) -> int:
    """Report foundation status/environment; never start an agent or backend."""
    parser = argparse.ArgumentParser(
        prog="python -m evolve",
        description="Evolve AI: офлайн-основа, этап 00. Модели пока не подключены.",
    )
    parser.add_argument("--config", type=Path, metavar="PATH",
                        help="локальный TOML-файл (перед командой)")
    commands = parser.add_subparsers(dest="command")
    doctor = commands.add_parser("doctor", help="проверить базовое окружение и конфигурацию")
    doctor.add_argument('--resources', action='store_true', help='офлайн-диагностика ресурсов')
    doctor.add_argument('--json', action='store_true', help='структурированный отчёт (с --resources)')
    commands.add_parser("status", help="показать фактическое состояние основы")
    commands.add_parser('demo', help='конечная имитация задач Core без LLM')
    args = parser.parse_args(argv)
    if args.command == 'doctor' and args.json and not args.resources:
        parser.error('--json требует --resources')
    if args.command is None:
        parser.print_help()
        return 0
    try:
        config = load_config(args.config)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return 2

    if args.command == 'demo':
        from evolve.core.demo import demo
        return demo()

    if args.command == 'doctor' and args.resources:
        import json
        from evolve.diagnostics import collect
        report = collect(Path(__file__).resolve().parents[1])
        if not args.json:
            print('Диагностика ресурсов: bytes — байты; null — неизвестно. Inference не проверен.')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"Evolve AI {__version__} | phase 00")
    print(f"Mode: {config.mode}")
    print(f"Config: {config.source if config.source else 'built-in offline defaults (evolve.toml absent)'}")
    if args.command == "doctor":
        os_label = sys.platform
        if sys.platform == "win32":
            version = sys.getwindowsversion()
            os_label = f"Windows {version.major}.{version.minor} (build {version.build})"
        print(f"OS: {os_label}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Working directory: {Path.cwd()}")
        print("GPU/Vulkan: not checked (phase 01)")
    else:
        print("State: idle (no agent loop)")
        print("Models: none (inference and mock backend not implemented)")
        print("External APIs: disabled (no adapters implemented)")
        print("Memory, tools, policy enforcement, evaluation, audit: not implemented")
    return 0
