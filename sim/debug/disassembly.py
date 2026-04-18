import subprocess
import re
from pathlib import Path
from typing import List

_INS_RE = re.compile(r"^\s*([0-9a-fA-F]+):\s")

def disasm_elf(elf_path: str) -> str:
    """
    Devuelve el desensamblado completo (texto) usando objdump.
    """
    p = Path(elf_path)
    if not p.exists():
        raise FileNotFoundError(f"No existe ELF: {elf_path}")
    return subprocess.check_output(
        ["arm-none-eabi-objdump", "-d", str(p)],
        text=True,
        errors="replace",
    )

def disasm_around_pc(elf_path: str, pc: int, context: int = 5) -> List[str]:
    """
    Devuelve líneas de objdump alrededor de la instrucción cuyo address == PC.
    Si no encuentra el PC exacto, usa la instrucción más cercana por debajo (previa).
    'context' = número de instrucciones antes y después.
    """
    txt = disasm_elf(elf_path)
    lines = txt.splitlines()

    # Extraer solo líneas de instrucciones con su address
    ins_lines = []
    ins_addrs = []

    for line in lines:
        m = _INS_RE.match(line)
        if m:
            addr = int(m.group(1), 16)
            ins_addrs.append(addr)
            ins_lines.append(line)

    if not ins_lines:
        return ["(No se encontraron instrucciones en el desensamblado)"]

    # Encontrar índice del PC (exacto o el anterior más cercano)
    idx = None
    for i, a in enumerate(ins_addrs):
        if a == pc:
            idx = i
            break

    if idx is None:
        # Buscar el mayor addr <= pc
        prev = -1
        for i, a in enumerate(ins_addrs):
            if a <= pc:
                prev = i
            else:
                break
        idx = prev if prev != -1 else 0

    start = max(0, idx - context)
    end = min(len(ins_lines), idx + context + 1)

    out = []
    out.append(f"Disasm around PC=0x{pc:08X} (±{context})")
    for i in range(start, end):
        prefix = "=> " if i == idx else "   "
        out.append(prefix + ins_lines[i])
    return out