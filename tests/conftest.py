from pathlib import Path

import pytest

from sim.core.session import DebugSession
from sim.debug.symbols import resolve_symbol
from sim.toolchain.gnu import BUILD_DIR, build_asm, toolchain_status


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def pytest_configure(config):
    missing = [item["tool"] for item in toolchain_status() if not item["found"]]
    if missing:
        pytest.exit(
            "Falta la toolchain ARM GNU necesaria para los tests: "
            + ", ".join(missing),
            returncode=2,
        )


@pytest.fixture
def build_example():
    def _build(relative_path: str, base: str = "0x00010000") -> tuple[Path, Path]:
        source = PROJECT_ROOT / relative_path
        build_asm(str(source), base, verbose=False)
        return BUILD_DIR / f"{source.stem}.elf", BUILD_DIR / f"{source.stem}.bin"

    return _build


@pytest.fixture
def loaded_session(build_example):
    def _load(relative_path: str) -> tuple[DebugSession, Path, Path]:
        elf_path, bin_path = build_example(relative_path)
        session = DebugSession()
        session.load(str(bin_path))
        return session, elf_path, bin_path

    return _load


@pytest.fixture
def symbol():
    def _symbol(elf_path: Path, name: str) -> int:
        return resolve_symbol(str(elf_path), name)

    return _symbol
