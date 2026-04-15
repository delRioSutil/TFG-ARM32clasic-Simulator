from pathlib import Path
from typing import Any

from sim.core.disasm import disasm_around_pc
from sim.core.symbols import resolve_symbol
from sim.core.toolchain import build_asm


class DebugSession:
    """Coordinates one interactive debugging session.

    The CLI should delegate stateful operations here instead of managing the
    backend, loaded artifacts and breakpoint resolution directly.
    """

    def __init__(self):
        from sim.core.backend_unicorn import UnicornBackend

        self.backend = UnicornBackend()
        self.current_elf: str | None = None
        self.current_bin: str | None = None

    def build(self, src: str, base: str = "0x00000000") -> dict[str, str]:
        build_asm(src, base)

        name = Path(src).stem
        self.current_elf = f"build/{name}.elf"
        self.current_bin = f"build/{name}.bin"

        return {
            "elf": self.current_elf,
            "bin": self.current_bin,
        }

    def load(self, bin_path: str, base: str = "0x00000000") -> None:
        self.backend.load_bin(bin_path, base)
        self.current_bin = bin_path

        if bin_path.endswith(".bin"):
            elf_guess = bin_path[:-4] + ".elf"
            if Path(elf_guess).exists():
                self.current_elf = elf_guess

    def step(self, count: int = 1) -> int:
        self.backend.step(count)
        return self.regs()["PC"]

    def regs(self) -> dict[str, int]:
        return self.backend.regs()

    def add_breakpoint(self, target: str) -> tuple[int, str | None]:
        if target.startswith(("0x", "0X")):
            self.backend.add_breakpoint(target)
            return int(target, 16), None

        if self.current_elf is None:
            raise ValueError(
                "No hay ELF asociado. Ejecuta primero 'build ...' o carga un .bin que tenga .elf al lado."
            )

        addr = resolve_symbol(self.current_elf, target)
        self.backend.add_breakpoint(hex(addr))
        return addr, target

    def list_breakpoints(self) -> list[int]:
        return sorted(self.backend.breakpoints)

    def run(self, max_steps: int = 100000) -> tuple[str, int]:
        reason = self.backend.run_until_break(max_steps=max_steps)
        return reason, self.regs()["PC"]

    def disasm(self, context: int = 5) -> list[str]:
        if self.current_elf is None:
            raise ValueError("No hay ELF asociado. Ejecuta 'build ...' primero.")

        pc = self.regs()["PC"]
        return disasm_around_pc(self.current_elf, pc, context=context)

    def last_exception(self) -> dict[str, Any] | None:
        return self.backend.last_exception
