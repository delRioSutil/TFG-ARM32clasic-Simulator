import sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_ALL
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
    UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
    UC_ARM_REG_CPSR
)

def usage():
    print("Uso:")
    print("  python tools/unicorn_run.py <bin_path> [base_hex] [steps]")
    print("Ejemplos:")
    print("  python tools/unicorn_run.py build/hello.bin 0x00000000 1")
    print("  python tools/unicorn_run.py build/mi_prog.bin 0x00010000 10")

def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    bin_path = Path(sys.argv[1])
    base = int(sys.argv[2], 16) if len(sys.argv) >= 3 else 0x00000000
    steps = int(sys.argv[3]) if len(sys.argv) >= 4 else 1

    if not bin_path.exists():
        print(f"Error: no existe {bin_path}")
        sys.exit(1)

    code = bin_path.read_bytes()

    # Memoria: mapea un bloque suficientemente grande a partir de base
    mem_size = 2 * 1024 * 1024  # 2MB
    mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    mu.mem_map(base, mem_size, UC_PROT_ALL)
    mu.mem_write(base, code)

    # Inicializa PC en base (asumimos _start en base según linker script)
    mu.reg_write(UC_ARM_REG_PC, base)

    # Ejecuta "steps" instrucciones (modo step)
    mu.emu_start(base, base + len(code), count=steps)

    regs = {
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

    print(f"BIN: {bin_path}  BASE=0x{base:08X}  STEPS={steps}")
    for k, v in regs.items():
        print(f"{k:>4} = 0x{v:08X}")

if __name__ == "__main__":
    main()
