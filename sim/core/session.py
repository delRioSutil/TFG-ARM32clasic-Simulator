from sim.core.disasm import disasm_around_pc
from sim.core.exceptions import ExceptionEvent
from sim.core.program import ProgramArtifact
from sim.core.symbols import resolve_symbol
from sim.core.toolchain import BUILD_DIR, build_asm


class DebugSession:
    """Coordinates one interactive debugging session.

    The CLI should delegate stateful operations here instead of managing the
    backend, loaded artifacts and breakpoint resolution directly.
    """

    def __init__(self):
        from sim.core.backend_unicorn import UnicornBackend

        self.backend = UnicornBackend()
        self.program: ProgramArtifact | None = None

    def build(self, src: str, base: str = "0x00000000") -> dict[str, str]:
        base_int = int(base, 0)
        build_asm(src, base)

        self.program = ProgramArtifact.from_source(src, base_int, BUILD_DIR)
        return self.program.as_cli_artifacts()

    def load(self, bin_path: str, base: str = "0x00000000") -> None:
        base_int = int(base, 0)
        self.backend.load_bin(bin_path, base)
        self.program = ProgramArtifact.from_binary(bin_path, base_int)

    def step(self, count: int = 1) -> int:
        self.backend.step(count)
        return self.regs()["PC"]

    def regs(self) -> dict[str, int]:
        return self.backend.regs()

    def add_breakpoint(self, target: str) -> tuple[int, str | None]:
        if target.startswith(("0x", "0X")):
            self.backend.add_breakpoint(target)
            return int(target, 16), None

        if self.program is None or self.program.elf_path is None:
            raise ValueError(
                "No hay ELF asociado. Ejecuta primero 'build ...' o carga un .bin que tenga .elf al lado."
            )

        addr = resolve_symbol(str(self.program.elf_path), target)
        self.backend.add_breakpoint(hex(addr))
        return addr, target

    def list_breakpoints(self) -> list[int]:
        return sorted(self.backend.breakpoints)

    def run(self, max_steps: int = 100000) -> tuple[str, int]:
        reason = self.backend.run_until_break(max_steps=max_steps)
        return reason, self.regs()["PC"]

    def disasm(self, context: int = 5) -> list[str]:
        if self.program is None or self.program.elf_path is None:
            raise ValueError("No hay ELF asociado. Ejecuta 'build ...' primero.")

        pc = self.regs()["PC"]
        return disasm_around_pc(str(self.program.elf_path), pc, context=context)

    def last_exception(self) -> ExceptionEvent | None:
        return self.backend.last_exception
