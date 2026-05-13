import json
from pathlib import Path
from typing import Any

from sim.exercises.exercise import Exercise, MemoryExpectation


DEFAULT_CONFIG_NAME = "checks.json"


def load_exercises(folder: str | Path, config_path: str | Path | None = None) -> list[Exercise]:
    base_dir = Path(folder)
    if not base_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta de ejercicios: {base_dir}")
    if not base_dir.is_dir():
        raise NotADirectoryError(f"No es una carpeta de ejercicios: {base_dir}")

    config = Path(config_path) if config_path is not None else base_dir / DEFAULT_CONFIG_NAME
    if not config.exists():
        raise FileNotFoundError(
            f"No existe la configuracion de correccion: {config}. "
            f"Crea un {DEFAULT_CONFIG_NAME} o usa --config."
        )

    raw = json.loads(config.read_text(encoding="utf-8"))
    defaults = raw.get("defaults", {})
    entries = raw.get("exercises")
    if not isinstance(entries, list):
        raise ValueError("La configuracion debe contener una lista 'exercises'.")

    exercises = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Entrada de ejercicio #{index} invalida.")
        exercises.append(_parse_exercise(base_dir, entry, defaults, index))

    return exercises


def _parse_exercise(
    base_dir: Path,
    entry: dict[str, Any],
    defaults: dict[str, Any],
    index: int,
) -> Exercise:
    filename = entry.get("file")
    if not isinstance(filename, str) or not filename:
        raise ValueError(f"El ejercicio #{index} no define 'file'.")

    source_path = base_dir / filename
    if not source_path.exists():
        raise FileNotFoundError(f"No existe el archivo del ejercicio: {source_path}")

    return Exercise(
        source_path=source_path,
        expected_registers=_parse_registers(entry.get("expected_registers", {})),
        expected_memory=_parse_memory(entry.get("expected_memory", [])),
        base=str(entry.get("base", defaults.get("base", "0x00010000"))),
        max_steps=int(entry.get("max_steps", defaults.get("max_steps", 1000))),
        stop_symbol=str(entry.get("stop_symbol", defaults.get("stop_symbol", "end"))),
    )


def _parse_registers(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        raise ValueError("'expected_registers' debe ser un objeto.")

    return {str(register).upper(): _parse_int(value) for register, value in raw.items()}


def _parse_memory(raw: Any) -> list[MemoryExpectation]:
    if not isinstance(raw, list):
        raise ValueError("'expected_memory' debe ser una lista.")

    expectations = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Entrada expected_memory #{index} invalida.")

        expectations.append(
            MemoryExpectation(
                address=_parse_int(item.get("address")),
                expected=_parse_expected_memory_value(item.get("expected")),
                size=int(item.get("size", 4)),
                byteorder=str(item.get("byteorder", "little")),
            )
        )

    return expectations


def _parse_expected_memory_value(value: Any) -> int | bytes | str:
    if value is None:
        raise ValueError("Cada expected_memory debe definir 'expected'.")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if value.strip().startswith(("0x", "0X")):
            return int(value, 0)
        return value
    if isinstance(value, list):
        return bytes(_parse_int(item) for item in value)
    raise ValueError(f"Valor de memoria esperado no soportado: {value!r}")


def _parse_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise ValueError(f"Valor entero invalido: {value!r}")
