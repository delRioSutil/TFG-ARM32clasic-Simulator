import struct
from unicorn import UcError, UC_ERR_INSN_INVALID, UC_HOOK_CODE
from pathlib import Path
from sim.core.exceptions import ExceptionEvent
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_ALL
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
    UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
    UC_ARM_REG_CPSR
)

class UnicornBackend:
    def __init__(self):
        self.mu = None
        self.base = None
        self.code_len = None
        self.breakpoints = set()
        self.vector_base = 0x00000000
        self._pending_exception = None
        self.last_exception = None
        self.spsr_svc = None

    def load_bin(self, bin_path: str, base_hex: str = "0x00000000", mem_size: int = 2 * 1024 * 1024):
        p = Path(bin_path)
        if not p.exists():
            raise FileNotFoundError(f"No existe: {bin_path}")

        code = p.read_bytes()
        base = int(base_hex, 16)

        mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        mu.mem_map(base, mem_size, UC_PROT_ALL)
        mu.mem_write(base, code)
        mu.reg_write(UC_ARM_REG_PC, base)

        self.mu = mu
        # Hook para ver cada instrucción y detectar SWI
        self.mu.hook_add(UC_HOOK_CODE, self._hook_code)
        self.base = base
        self.code_len = len(code)

    def step(self, n: int = 1):
        self.last_exception = None
        self._pending_exception = None
        if self.mu is None:
            raise RuntimeError("No hay programa cargado. Usa 'load' primero.")
        pc = self.mu.reg_read(UC_ARM_REG_PC)
        # Ejecuta n instrucciones desde el PC actual
        try:
             self.mu.emu_start(pc, self.base + self.code_len, count=n)
        except UcError as e:
            # Undefined instruction (mínimo)
            if e.errno == UC_ERR_INSN_INVALID:
                self._pending_exception = ("UNDEF", pc, None)
            else:
                raise

        # Si hubo excepción detectada por hook o por error, entra en excepción
        if self._pending_exception:
            etype, at_pc, extra = self._pending_exception
            self._enter_exception(etype, at_pc, extra)

    def regs(self) -> dict:
        if self.mu is None:
            raise RuntimeError("No hay programa cargado. Usa 'load' primero.")

        mu = self.mu
        return {
            "R0": mu.reg_read(UC_ARM_REG_R0),
            "R1": mu.reg_read(UC_ARM_REG_R1),
            "R2": mu.reg_read(UC_ARM_REG_R2),
            "R3": mu.reg_read(UC_ARM_REG_R3),
            "R4": mu.reg_read(UC_ARM_REG_R4),
            "R5": mu.reg_read(UC_ARM_REG_R5),
            "R6": mu.reg_read(UC_ARM_REG_R6),
            "R7": mu.reg_read(UC_ARM_REG_R7),
            "R8": mu.reg_read(UC_ARM_REG_R8),
            "R9": mu.reg_read(UC_ARM_REG_R9),
            "R10": mu.reg_read(UC_ARM_REG_R10),
            "R11": mu.reg_read(UC_ARM_REG_R11),
            "R12": mu.reg_read(UC_ARM_REG_R12),
            "SP": mu.reg_read(UC_ARM_REG_SP),
            "LR": mu.reg_read(UC_ARM_REG_LR),
            "PC": mu.reg_read(UC_ARM_REG_PC),
            "CPSR": mu.reg_read(UC_ARM_REG_CPSR),
        }
    
    def add_breakpoint(self, addr_hex: str):
        addr = int(addr_hex, 16)
        self.breakpoints.add(addr)

    def clear_breakpoints(self):
        self.breakpoints.clear()

    def run_until_break(self, max_steps: int = 100000):
        """
        Ejecuta instrucción a instrucción hasta:
        - llegar a un breakpoint (PC == addr)
        - o consumir max_steps
        Devuelve: "break" o "max"
        """
        if self.mu is None:
            raise RuntimeError("No hay programa cargado. Usa 'load' primero.")

        for _ in range(max_steps):
            pc = self.mu.reg_read(UC_ARM_REG_PC)
            if pc in self.breakpoints:
                return "break"
            self.step(1)
            if self.last_exception is not None:
                return "exception"
        return "max"

    def _hook_code(self, uc, address, size, user_data=None):
        # Por ahora solo ARM (4 bytes). Thumb lo trataremos más adelante.
        if size != 4:
            return

        try:
            insn = uc.mem_read(address, size)
        except Exception:
            return

        opcode = struct.unpack("<I", insn)[0]

        # ARM SWI encoding: 0xEF000000 | imm24
        if (opcode & 0xFF000000) == 0xEF000000:
            imm24 = opcode & 0x00FFFFFF
            self._pending_exception = ("SWI", address, imm24)
            uc.emu_stop()  # paramos para que el "step/run" devuelva control al usuario

    def _enter_exception(self, etype: str, at_pc: int, imm=None):
        # Lee CPSR actual
        cpsr = self.mu.reg_read(UC_ARM_REG_CPSR)

        if etype == "SWI":
            # Guarda CPSR en SPSR_svc (modelo mínimo)
            self.spsr_svc = cpsr

            # LR_svc = dirección de retorno (PC + 4 en ARM)
            self.mu.reg_write(UC_ARM_REG_LR, at_pc + 4)

            # Cambia modo a SVC (0x13) y enmascara IRQ (I=1)
            new_cpsr = (cpsr & ~0x1F) | 0x13
            new_cpsr |= (1 << 7)  # I bit
            self.mu.reg_write(UC_ARM_REG_CPSR, new_cpsr)

            # Salta al vector SWI = base + 0x08
            vec = self.vector_base + 0x08
            self.mu.reg_write(UC_ARM_REG_PC, vec)

            self.last_exception = ExceptionEvent(
                type="SWI",
                pc=at_pc,
                vector=vec,
                imm24=imm,
                cpsr_before=cpsr,
                cpsr_after=new_cpsr,
                lr=at_pc + 4,
                explanation="SWI/SVC transfiere el control al vector 0x08 en modo supervisor.",
            )
            return

        # Placeholder para futuras excepciones
        self.last_exception = ExceptionEvent(
            type=etype,
            pc=at_pc,
            vector=None,
            cpsr_before=cpsr,
            cpsr_after=cpsr,
            explanation="Excepcion detectada por el backend; el tratamiento completo queda pendiente.",
        )
