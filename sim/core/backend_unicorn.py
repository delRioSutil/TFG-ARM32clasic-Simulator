from pathlib import Path
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
        self.base = base
        self.code_len = len(code)

    def step(self, n: int = 1):
        if self.mu is None:
            raise RuntimeError("No hay programa cargado. Usa 'load' primero.")
        pc = self.mu.reg_read(UC_ARM_REG_PC)
        # Ejecuta n instrucciones desde el PC actual
        self.mu.emu_start(pc, self.base + self.code_len, count=n)

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
