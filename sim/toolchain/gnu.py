import subprocess
import os
import shutil
import sys
from pathlib import Path


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _project_root()
BUILD_DIR = PROJECT_ROOT / "build"
TOOLCHAIN_ENV = "ARM32SIM_TOOLCHAIN_BIN"
REQUIRED_TOOLCHAIN_TOOLS = [
    "arm-none-eabi-as",
    "arm-none-eabi-ld",
    "arm-none-eabi-objcopy",
    "arm-none-eabi-objdump",
    "arm-none-eabi-nm",
]

LOCAL_TOOLCHAIN_DIRS = [
    PROJECT_ROOT / "runtime" / "toolchain" / "bin",
    PROJECT_ROOT / "tools" / "toolchain" / "bin",
]


def _parse_base(base: str) -> int:
    try:
        return int(base, 0)
    except ValueError:
        return int(base, 16)


def _candidate_toolchain_dirs() -> list[tuple[Path, str]]:
    dirs = []
    env_path = os.environ.get(TOOLCHAIN_ENV)
    if env_path:
        dirs.append((Path(env_path), f"{TOOLCHAIN_ENV}"))

    for directory in LOCAL_TOOLCHAIN_DIRS:
        dirs.append((directory, "local"))

    return dirs


def _tool_names(tool_name: str) -> list[str]:
    names = [tool_name]
    if os.name == "nt" and not tool_name.endswith(".exe"):
        names.append(f"{tool_name}.exe")
    return names


def _find_tool(tool_name: str) -> tuple[str | None, str | None]:
    for directory, source in _candidate_toolchain_dirs():
        for name in _tool_names(tool_name):
            candidate = directory / name
            if candidate.exists():
                return str(candidate), source

    found = shutil.which(tool_name)
    if found:
        return found, "PATH"

    return None, None


def _tool_path(tool_name: str) -> str:
    path, _source = _find_tool(tool_name)
    if path:
        return path

    raise FileNotFoundError(
        "No se encontro la herramienta "
        f"{tool_name}. Esperada en runtime/toolchain/bin, "
        f"tools/toolchain/bin, {TOOLCHAIN_ENV} o en el PATH."
    )


def toolchain_status() -> list[dict[str, str | bool | None]]:
    status = []
    for tool in REQUIRED_TOOLCHAIN_TOOLS:
        path, source = _find_tool(tool)
        status.append(
            {
                "tool": tool,
                "found": path is not None,
                "path": path,
                "source": source,
            }
        )
    return status


def _run(cmd: list[str], verbose: bool = True) -> None:
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

    if verbose and result.stdout:
        print(result.stdout, end="")
    if verbose and result.stderr:
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


def build_asm(src: str, base: str = "0x00010000", verbose: bool = True) -> None:
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

    if verbose:
        print(f"[1/3] Assembling: {src_path} -> {obj_path}")
    _run([assembler, "-o", str(obj_path), str(src_path)], verbose=verbose)

    if verbose:
        print(f"[2/3] Linking: {obj_path} -> {elf_path} (BASE=0x{base_int:08X})")
    _run([linker, "-T", str(linker_path), "-o", str(elf_path), str(obj_path)], verbose=verbose)

    if verbose:
        print(f"[3/3] Objcopy: {elf_path} -> {bin_path}")
    _run([objcopy, "-O", "binary", str(elf_path), str(bin_path)], verbose=verbose)

    if verbose:
        print("OK")
        print(f"  ELF: {elf_path}")
        print(f"  BIN: {bin_path}")
