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
    UC_ARM_REG_CPSR, UC_ARM_REG_SPSR
)


EPD6_LOAD_ADDRESS = 0x00010000
EPD6_VECTOR_BASE = 0x00000000
EPD6_VECTOR_SIZE = 0x20
EPD6_RAM_BASE = 0x00000000
EPD6_RAM_SIZE = 0x00800000
EPD6_UART_BASE = 0x101F1000
EPD6_UART_SIZE = 0x1000
EPD6_UARTDR = 0x101F1000
EPD6_UARTFR = 0x101F1018

ARM_MODE_USER = 0x10
ARM_MODE_FIQ = 0x11
ARM_MODE_IRQ = 0x12
ARM_MODE_SVC = 0x13
ARM_MODE_ABT = 0x17
ARM_MODE_UND = 0x1B
ARM_MODE_SYS = 0x1F

EPD6_STACKS = [
    (ARM_MODE_FIQ, 0x00100000),
    (ARM_MODE_IRQ, 0x00200000),
    (ARM_MODE_SVC, 0x00300000),
    (ARM_MODE_ABT, 0x00400000),
    (ARM_MODE_UND, 0x00500000),
    (ARM_MODE_SYS, 0x00600000),
    (ARM_MODE_USER, 0x00700000),
]

ARM_INSTRUCTION_SIZE = 4
ARM_COND_AL = 0xE
ARM_COND_NV = 0xF
ARM_CPSR_N = 1 << 31
ARM_CPSR_Z = 1 << 30
ARM_CPSR_C = 1 << 29
ARM_CPSR_V = 1 << 28


class UnicornBackend:
    def __init__(self):
        self.mu = None
        self.base = None
        self.code_len = None
        self.breakpoints = set()
        self._temporary_breakpoints = set()
        self.vector_base = 0x00000000
        self.exception_handlers = {}
        self._pending_exception = None
        self.last_exception = None
        self.spsr_svc = None

    def load_bin(
        self,
        bin_path: str,
        base_hex: str = "0x00010000",
        mem_size: int = EPD6_RAM_SIZE,
        entry_point: int | None = None,
        exception_handlers: dict[str, int] | None = None,
    ):
        p = Path(bin_path)
        if not p.exists():
            raise FileNotFoundError(f"No existe: {bin_path}")

        code = p.read_bytes()
        base = int(base_hex, 0)

        mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        mu.mem_map(EPD6_RAM_BASE, mem_size, UC_PROT_ALL)
        mu.mem_map(EPD6_UART_BASE, EPD6_UART_SIZE, UC_PROT_ALL)
        mu.mem_write(base, code)

        self.mu = mu
        self._copy_vectors_to_zero(code, base)
        self._configure_epd6_stacks()
        self._enter_user_mode()
        mu.reg_write(UC_ARM_REG_PC, entry_point if entry_point is not None else base)
        # Hook para ver cada instrucción y detectar SWI
        self.mu.hook_add(UC_HOOK_CODE, self._hook_code)
        self.base = base
        self.code_len = len(code)
        self.vector_base = EPD6_VECTOR_BASE
        self.exception_handlers = exception_handlers or {}

    def _copy_vectors_to_zero(self, code: bytes, base: int):
        if base == EPD6_VECTOR_BASE or len(code) < EPD6_VECTOR_SIZE:
            return
        self.mu.mem_write(EPD6_VECTOR_BASE, code[:EPD6_VECTOR_SIZE])

    def _configure_epd6_stacks(self):
        for mode, sp in EPD6_STACKS:
            self._set_mode(mode)
            self.mu.reg_write(UC_ARM_REG_SP, sp)

    def _enter_user_mode(self):
        self._set_mode(ARM_MODE_USER)

    def _set_mode(self, mode: int):
        cpsr = self.mu.reg_read(UC_ARM_REG_CPSR)
        self.mu.reg_write(UC_ARM_REG_CPSR, (cpsr & ~0x1F) | mode)

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

    def next(self, max_steps: int = 100000):
        """Step over calls and software exceptions."""
        self._ensure_loaded()
        pc = self.mu.reg_read(UC_ARM_REG_PC)
        opcode = self._read_instruction(pc)
        if not self._instruction_will_execute(opcode):
            self.step(1)
            return "step"

        is_swi = self._is_software_interrupt(opcode)
        if not self._is_call_instruction(opcode) and not is_swi:
            self.step(1)
            return "step"

        return_pc = pc + ARM_INSTRUCTION_SIZE
        return self._run_until_temporary_breakpoint(
            return_pc,
            max_steps,
            stop_on_exception=not is_swi,
        )

    def finish(self, max_steps: int = 100000):
        """Continue until the address currently stored in LR."""
        self._ensure_loaded()
        lr = self.mu.reg_read(UC_ARM_REG_LR)
        if lr == 0:
            raise RuntimeError("No hay direccion de retorno valida en LR.")
        if lr % ARM_INSTRUCTION_SIZE != 0:
            raise RuntimeError(f"LR no contiene una direccion ARM alineada: 0x{lr:08X}")

        return self._run_until_temporary_breakpoint(lr, max_steps)

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

    def read_memory(self, address: int, size: int) -> bytes:
        self._ensure_loaded()
        if size <= 0:
            raise ValueError("El tamaño de memoria debe ser mayor que cero.")

        try:
            return bytes(self.mu.mem_read(address, size))
        except UcError as exc:
            raise RuntimeError(
                f"No se pudo leer memoria en 0x{address:08X} con tamaño {size}."
            ) from exc
    
    def add_breakpoint(self, addr_hex: str):
        addr = int(addr_hex, 16)
        self.breakpoints.add(addr)

    def clear_breakpoints(self):
        self.breakpoints.clear()

    def run_until_break(self, max_steps: int = 100000, stop_on_exception: bool = True):
        """
        Ejecuta instrucción a instrucción hasta:
        - llegar a un breakpoint (PC == addr)
        - o consumir max_steps
        Devuelve: "break" o "max"
        """
        self._ensure_loaded()

        for _ in range(max_steps):
            pc = self.mu.reg_read(UC_ARM_REG_PC)
            if pc in self.breakpoints or pc in self._temporary_breakpoints:
                return "break"
            self.step(1)
            if stop_on_exception and self.last_exception is not None:
                return "exception"
        return "max"

    def _run_until_temporary_breakpoint(
        self,
        addr: int,
        max_steps: int,
        stop_on_exception: bool = True,
    ):
        self._temporary_breakpoints.add(addr)
        try:
            return self.run_until_break(
                max_steps=max_steps,
                stop_on_exception=stop_on_exception,
            )
        finally:
            self._temporary_breakpoints.discard(addr)

    def _ensure_loaded(self):
        if self.mu is None:
            raise RuntimeError("No hay programa cargado. Usa 'load' primero.")

    def _read_instruction(self, address: int) -> int:
        raw = self.mu.mem_read(address, ARM_INSTRUCTION_SIZE)
        return struct.unpack("<I", raw)[0]

    def _is_call_instruction(self, opcode: int) -> bool:
        # BL/BLX immediate: cond 101x... with link bit set. cond=1111 is BLX.
        if (opcode & 0x0E000000) == 0x0A000000 and (opcode & (1 << 24)):
            return True

        # BLX register: xxxx000100101111111111110011xxxx
        return (opcode & 0x0FFFFFF0) == 0x012FFF30

    def _is_software_interrupt(self, opcode: int) -> bool:
        # ARM SVC/SWI: cond 1111 imm24
        return (opcode & 0x0F000000) == 0x0F000000 and self._condition_code(opcode) != ARM_COND_NV

    def _instruction_will_execute(self, opcode: int) -> bool:
        if self._is_blx_immediate(opcode):
            return True
        return self._condition_passed(opcode)

    def _is_blx_immediate(self, opcode: int) -> bool:
        return self._condition_code(opcode) == ARM_COND_NV and (opcode & 0x0E000000) == 0x0A000000

    def _condition_code(self, opcode: int) -> int:
        return (opcode >> 28) & 0xF

    def _condition_passed(self, opcode: int) -> bool:
        cond = self._condition_code(opcode)
        cpsr = self.mu.reg_read(UC_ARM_REG_CPSR)
        n = bool(cpsr & ARM_CPSR_N)
        z = bool(cpsr & ARM_CPSR_Z)
        c = bool(cpsr & ARM_CPSR_C)
        v = bool(cpsr & ARM_CPSR_V)

        if cond == 0x0:
            return z
        if cond == 0x1:
            return not z
        if cond == 0x2:
            return c
        if cond == 0x3:
            return not c
        if cond == 0x4:
            return n
        if cond == 0x5:
            return not n
        if cond == 0x6:
            return v
        if cond == 0x7:
            return not v
        if cond == 0x8:
            return c and not z
        if cond == 0x9:
            return not c or z
        if cond == 0xA:
            return n == v
        if cond == 0xB:
            return n != v
        if cond == 0xC:
            return not z and n == v
        if cond == 0xD:
            return z or n != v
        if cond == ARM_COND_AL:
            return True
        return False

    def _hook_code(self, uc, address, size, user_data=None):
        # Por ahora solo ARM (4 bytes). Thumb lo trataremos más adelante.
        if size != 4:
            return

        try:
            insn = uc.mem_read(address, size)
        except Exception:
            return

        opcode = struct.unpack("<I", insn)[0]

        # ARM SWI/SVC encoding: cond 1111 imm24. Solo dispara si la condicion pasa.
        if self._is_software_interrupt(opcode) and self._condition_passed(opcode):
            imm24 = opcode & 0x00FFFFFF
            self._pending_exception = ("SWI", address, imm24)
            uc.emu_stop()  # paramos para que el "step/run" devuelva control al usuario

    def _enter_exception(self, etype: str, at_pc: int, imm=None):
        # Lee CPSR actual
        cpsr = self.mu.reg_read(UC_ARM_REG_CPSR)

        if etype == "SWI":
            # Guarda CPSR en SPSR_svc (modelo mínimo)
            self.spsr_svc = cpsr

            # Cambia modo a SVC (0x13) y enmascara IRQ (I=1)
            new_cpsr = (cpsr & ~0x1F) | 0x13
            new_cpsr |= (1 << 7)  # I bit
            self.mu.reg_write(UC_ARM_REG_CPSR, new_cpsr)
            self.mu.reg_write(UC_ARM_REG_SPSR, cpsr)

            # LR_svc = dirección de retorno (PC + 4 en ARM)
            self.mu.reg_write(UC_ARM_REG_LR, at_pc + 4)

            # Salta al manejador SWI conocido si existe; si no, al vector SWI = base + 0x08.
            vec = self.vector_base + 0x08
            target = self.exception_handlers.get("SWI", vec)
            self.mu.reg_write(UC_ARM_REG_PC, target)

            self.last_exception = ExceptionEvent(
                type="SWI",
                pc=at_pc,
                vector=vec,
                handler=target,
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
