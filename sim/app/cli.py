import argparse
import importlib.metadata
import importlib.util
import platform
import shlex
import sys

from sim.toolchain.gnu import TOOLCHAIN_ENV, build_asm, toolchain_status

HELP = """
Comandos:
  build <file.s> [--base 0x00010000]
  load <file.bin> [--base 0x00010000]
  step [n] | si [n] | stepinto [n]
  next [max_steps] | so [max_steps] | stepover [max_steps]
  finish [max_steps] | stepout [max_steps]
  regs
  disasm [n]
  exc
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
                    if e.type == "SWI":
                        print(
                            f"EXC SWI at PC=0x{e.pc:08X} imm=0x{e.imm24:06X} "
                            f"vector=0x{e.vector:08X} handler=0x{e.handler:08X}"
                        )
                    else:
                        print(f"EXC {e.type} at PC=0x{e.pc:08X}")

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

if __name__ == "__main__":
    main()
