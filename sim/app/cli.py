import argparse
import importlib.metadata
import importlib.util
import platform
import shlex
import sys

from sim.toolchain.gnu import TOOLCHAIN_ENV, build_asm, toolchain_status

HELP = """
Comandos:
  build <file.s>
  load <file.bin>
  step [n] | si [n] | stepinto [n]
  next [max_steps] | so [max_steps] | stepover [max_steps]
  finish [max_steps] | stepout [max_steps]
  regs
  mem <0xADDR> [size]
  disasm [n]
  exc
  reset
  irq
  fiq
  quit
  break <0xADDR>
  bl
  run [max_steps]
  doctor
"""


def print_doctor() -> None:
    print("Python:")
    print(f"  OK   version: {platform.python_version()}")
    print(f"  OK   executable: {sys.executable}")
    print()

    print("Dependencias Python:")
    unicorn_spec = importlib.util.find_spec("unicorn")
    if unicorn_spec is None:
        print("  MISS unicorn")
        print("       Instala dependencias de desarrollo con:")
        print("       python -m pip install -r requirements.txt")
    else:
        try:
            unicorn_version = importlib.metadata.version("unicorn")
        except importlib.metadata.PackageNotFoundError:
            unicorn_version = "version desconocida"
        origin = unicorn_spec.origin or "ruta desconocida"
        print(f"  OK   unicorn: {unicorn_version} ({origin})")

    print()
    print("Toolchain ARM GNU:")
    ok = True
    for item in toolchain_status():
        if item["found"]:
            print(f'  OK   {item["tool"]}: {item["path"]} ({item["source"]})')
        else:
            ok = False
            print(f'  MISS {item["tool"]}')

    if not ok:
        print()
        print("No se encontro la toolchain completa.")
        print("Para modo autocontenido Windows, coloca los ejecutables en:")
        print("  runtime/toolchain/bin/")
        print("O define la variable de entorno:")
        print(f"  {TOOLCHAIN_ENV}=C:\\ruta\\a\\arm-none-eabi\\bin")


def format_memory_dump(address: int, data: bytes, row_size: int = 16) -> list[str]:
    lines = []
    for offset in range(0, len(data), row_size):
        chunk = data[offset : offset + row_size]
        hex_bytes = " ".join(f"{byte:02X}" for byte in chunk)
        ascii_text = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in chunk)
        lines.append(f"0x{address + offset:08X}: {hex_bytes:<47}  {ascii_text}")
    return lines


def run_check(folder: str, config: str | None = None) -> int:
    from sim.exercises.loader import load_exercises
    from sim.exercises.runner import ExerciseRunner

    exercises = load_exercises(folder, config)
    runner = ExerciseRunner()
    all_passed = True

    for exercise in exercises:
        result = runner.run(exercise)
        all_passed = all_passed and result.passed
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {exercise.source_path.name} ({result.run_reason}) PC=0x{result.final_pc:08X}")
        for check in result.checks:
            print(f"  {check.message}")

    return 0 if all_passed else 1

def repl():
    from sim.core.session import DebugSession

    session = DebugSession()
    print("ARM32 Teaching Simulator (CLI interactive)")
    print("Escribe 'help' para ver comandos.")

    while True:
        try:
            line = input("sim> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        if line in ("quit", "exit"):
            break

        if line == "help":
            print(HELP)
            continue

        parts = shlex.split(line)
        cmd = parts[0]

        try:
            if cmd == "build":
                p = argparse.ArgumentParser(prog="build", add_help=False)
                p.add_argument("src")
                p.add_argument("--base", default="0x00010000")
                a = p.parse_args(parts[1:])
                artifacts = session.build(a.src, a.base)
                print(f'ELF: {artifacts["elf"]}')
                print(f'BIN: {artifacts["bin"]}')
                print("OK: build terminado")

            elif cmd == "doctor":
                print_doctor()

            elif cmd == "load":
                p = argparse.ArgumentParser(prog="load", add_help=False)
                p.add_argument("bin")
                p.add_argument("--base", default="0x00010000")
                a = p.parse_args(parts[1:])
                session.load(a.bin, a.base)
                print(f"OK: cargado {a.bin} en base {a.base}")

            elif cmd in ("step", "si", "stepinto"):
                n = 1
                if len(parts) >= 2:
                    n = int(parts[1])
                pc = session.step(n)
                print(f"OK: step {n} (PC=0x{pc:08X})")

            elif cmd in ("next", "so", "stepover"):
                max_steps = int(parts[1]) if len(parts) >= 2 else 100000
                reason, pc = session.next(max_steps=max_steps)
                print(f"OK: next terminado ({reason}) PC=0x{pc:08X}")

            elif cmd in ("finish", "stepout"):
                max_steps = int(parts[1]) if len(parts) >= 2 else 100000
                reason, pc = session.finish(max_steps=max_steps)
                print(f"OK: finish terminado ({reason}) PC=0x{pc:08X}")

            elif cmd == "regs":
                r = session.regs()
                for k, v in r.items():
                    print(f"{k:>4} = 0x{v:08X}")

            elif cmd == "mem":
                if len(parts) not in (2, 3):
                    raise ValueError("Uso: mem <0xADDR> [size]")
                address = int(parts[1], 0)
                size = int(parts[2], 0) if len(parts) == 3 else 64
                data = session.memory(address, size)
                for line in format_memory_dump(address, data):
                    print(line)
            
            elif cmd == "break":
                if len(parts) != 2:
                    raise ValueError("Uso: break 0xADDR | break <symbol>")
                target = parts[1]
                addr, symbol = session.add_breakpoint(target)
                if symbol is None:
                    print(f"OK: breakpoint en {target}")
                else:
                    print(f"OK: breakpoint en {symbol} (0x{addr:08X})")

            elif cmd == "bl":
                bps = session.list_breakpoints()
                if not bps:
                    print("(sin breakpoints)")
                else:
                    for a in bps:
                        print(f"* 0x{a:08X}")

            elif cmd == "run":
                max_steps = int(parts[1]) if len(parts) >= 2 else 100000
                reason, pc = session.run(max_steps=max_steps)
                print(f"OK: run terminado ({reason}) PC=0x{pc:08X}")

            elif cmd == "reset":
                pc = session.reset()
                print(f"OK: reset simulado PC=0x{pc:08X}")

            elif cmd == "irq":
                pc = session.irq()
                print(f"OK: IRQ simulada PC=0x{pc:08X}")

            elif cmd == "fiq":
                pc = session.fiq()
                print(f"OK: FIQ simulada PC=0x{pc:08X}")

            elif cmd == "disasm":
                ctx = 5
                if len(parts) >= 2:
                    ctx = int(parts[1])
                out_lines = session.disasm(context=ctx)
                for l in out_lines:
                    print(l)

            elif cmd == "exc":
                e = session.last_exception()
                if e is None:
                    print("(no exception)")
                else:
                    line = (
                        f"EXC {e.type} at PC=0x{e.pc:08X} "
                        f"vector=0x{e.vector:08X} handler=0x{e.handler:08X}"
                    )
                    if e.lr is not None:
                        line += f" LR=0x{e.lr:08X}"
                    if e.imm24 is not None:
                        line += f" imm=0x{e.imm24:06X}"
                    if e.fault_address is not None:
                        line += f" fault=0x{e.fault_address:08X}"
                    if e.fault_access is not None:
                        line += f" access={e.fault_access}"
                    print(line)

            else:
                print("Comando desconocido. Escribe 'help'.")

        except Exception as e:
            print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(prog="sim")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("repl", help="Modo interactivo (mantiene estado)")
    sub.add_parser("doctor", help="Comprueba dependencias externas")
    p_build = sub.add_parser("build", help="Build (one-shot)")
    p_build.add_argument("src")
    p_build.add_argument("--base", default="0x00010000")
    p_check = sub.add_parser("check", help="Corrige ejercicios desde una carpeta")
    p_check.add_argument("folder")
    p_check.add_argument("--config")

    args = parser.parse_args()

    if args.cmd == "repl":
        repl()
        return

    if args.cmd == "build":
        build_asm(args.src, args.base)
        print("OK: build terminado")
        return

    if args.cmd == "doctor":
        print_doctor()
        return

    if args.cmd == "check":
        raise SystemExit(run_check(args.folder, args.config))

if __name__ == "__main__":
    main()
