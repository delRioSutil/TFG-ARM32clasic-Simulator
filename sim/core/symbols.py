import subprocess
from pathlib import Path

def resolve_symbol(elf_path: str, symbol: str) -> int:
    """
    Devuelve la dirección (int) de un símbolo en un ELF usando arm-none-eabi-nm.
    Lanza ValueError si no existe.
    """
    p = Path(elf_path)
    if not p.exists():
        raise FileNotFoundError(f"No existe ELF: {elf_path}")

    # nm output: "00000008 T bp_here"
    out = subprocess.check_output(["arm-none-eabi-nm", str(p)], text=True, errors="replace")
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[2] == symbol:
            return int(parts[0], 16)

    raise ValueError(f"Símbolo no encontrado: {symbol}")
