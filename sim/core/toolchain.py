import subprocess
from pathlib import Path

def build_asm(src: str, base: str = "0x00000000") -> None:
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"No existe: {src}")

    cmd = ["bash", "tools/build.sh", str(src_path), base]
    subprocess.run(cmd, check=True)
