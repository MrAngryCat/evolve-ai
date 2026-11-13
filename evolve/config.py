"""Read and validate the foundation's local configuration without side effects."""

from dataclasses import dataclass
from pathlib import Path
import tomllib


class ConfigError(ValueError):
    """Configuration could not be loaded safely."""


@dataclass(frozen=True)
class Config:
    mode: str = "offline"
    source: Path | None = None


def load_config(path: Path | None = None) -> Config:
    """Missing default uses built-ins; an explicit missing path is an error."""
    candidate = path if path is not None else Path("evolve.toml")
    try:
        with candidate.open("rb") as stream:
            raw = stream.read(16385)
    except FileNotFoundError:
        if path is None:
            return Config()
        raise ConfigError("Указанный файл не найден.") from None
    except OSError:
        raise ConfigError("Не удалось прочитать файл.") from None

    if len(raw) > 16384:
        raise ConfigError("Размер файла превышает 16 КиБ.")
    try:
        data = tomllib.loads(raw.decode("utf-8-sig"))
    except (ValueError, RecursionError):
        # Includes decoding/TOML errors and parser resource limits. Errors may
        # contain configuration contents; never echo them or relax limits.
        raise ConfigError("Нужен корректный TOML в кодировке UTF-8.") from None

    if set(data) - {"evolve"}:
        raise ConfigError("Допустима только секция [evolve].")
    section = data.get("evolve", {})
    if not isinstance(section, dict) or set(section) - {"mode"}:
        raise ConfigError("В секции [evolve] допустим только параметр mode.")
    mode = section.get("mode", "offline")
    if mode not in ("offline", "mock"):
        raise ConfigError("Параметр mode должен быть offline или mock.")
    return Config(mode=mode, source=candidate.resolve())
