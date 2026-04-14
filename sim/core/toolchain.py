import subprocess
import os
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = PROJECT_ROOT / "build"

LOCAL_TOOLCHAIN_DIRS = [
    PROJECT_ROOT / "runtime" / "toolchain" / "bin",
    PROJECT_ROOT / "tools" / "toolchain" / "bin",
]


def _parse_base(base: str) -> int:
    try:
        return int(base, 0)
    except ValueError:
        return int(base, 16)


def _tool_path(tool_name: str) -> str:
    names = [tool_name]
    if os.name == "nt" and not tool_name.endswith(".exe"):
        names.append(f"{tool_name}.exe")

    for directory in LOCAL_TOOLCHAIN_DIRS:
        for name in names:
            candidate = directory / name
            if candidate.exists():
                return str(candidate)

    found = shutil.which(tool_name)
    if found:
        return found

    raise FileNotFoundError(
        "No se encontro la herramienta "
        f"{tool_name}. Esperada en runtime/toolchain/bin, "
        "tools/toolchain/bin o en el PATH."
    )


def _run(cmd: list[str]) -> None:
    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        if details:
            raise RuntimeError(details) from exc
        raise RuntimeError(f"Fallo el comando: {' '.join(cmd)}") from exc

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")


def _write_linker_script(path: Path, base_int: int) -> None:
    base_hex = f"0x{base_int:08X}"
    path.write_text(
        "\n".join(
            [
                "ENTRY(_start)",
                "",
                "SECTIONS",
                "{",
                f"  . = {base_hex};",
                "  .text : { *(.text*) }",
                "  .rodata : { *(.rodata*) }",
                "  .data : { *(.data*) }",
                "  .bss : { *(.bss*) *(COMMON) }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_asm(src: str, base: str = "0x00000000") -> None:
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"No existe: {src}")

    base_int = _parse_base(base)
    name = src_path.stem

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    obj_path = BUILD_DIR / f"{name}.o"
    elf_path = BUILD_DIR / f"{name}.elf"
    bin_path = BUILD_DIR / f"{name}.bin"
    linker_path = BUILD_DIR / f"linker_{name}.ld"

    assembler = _tool_path("arm-none-eabi-as")
    linker = _tool_path("arm-none-eabi-ld")
    objcopy = _tool_path("arm-none-eabi-objcopy")

    _write_linker_script(linker_path, base_int)

    print(f"[1/3] Assembling: {src_path} -> {obj_path}")
    _run([assembler, "-o", str(obj_path), str(src_path)])

    print(f"[2/3] Linking: {obj_path} -> {elf_path} (BASE=0x{base_int:08X})")
    _run([linker, "-T", str(linker_path), "-o", str(elf_path), str(obj_path)])

    print(f"[3/3] Objcopy: {elf_path} -> {bin_path}")
    _run([objcopy, "-O", "binary", str(elf_path), str(bin_path)])

    print("OK")
    print(f"  ELF: {elf_path}")
    print(f"  BIN: {bin_path}")
