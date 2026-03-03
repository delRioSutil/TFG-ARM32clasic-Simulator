import argparse
import shlex

from sim.core.toolchain import build_asm
from sim.core.backend_unicorn import UnicornBackend

HELP = """
Comandos:
  build <file.s> [--base 0x00000000]
  load <file.bin> [--base 0x00000000]
  step [n]
  regs
  quit
"""

def repl():
    backend = UnicornBackend()
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
                p.add_argument("--base", default="0x00000000")
                a = p.parse_args(parts[1:])
                build_asm(a.src, a.base)
                print("OK: build terminado")

            elif cmd == "load":
                p = argparse.ArgumentParser(prog="load", add_help=False)
                p.add_argument("bin")
                p.add_argument("--base", default="0x00000000")
                a = p.parse_args(parts[1:])
                backend.load_bin(a.bin, a.base)
                print(f"OK: cargado {a.bin} en base {a.base}")

            elif cmd == "step":
                n = 1
                if len(parts) >= 2:
                    n = int(parts[1])
                backend.step(n)
                pc = backend.regs()["PC"]
                print(f"OK: step {n} (PC=0x{pc:08X})")

            elif cmd == "regs":
                r = backend.regs()
                for k, v in r.items():
                    print(f"{k:>4} = 0x{v:08X}")

            else:
                print("Comando desconocido. Escribe 'help'.")

        except Exception as e:
            print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(prog="sim")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("repl", help="Modo interactivo (mantiene estado)")
    p_build = sub.add_parser("build", help="Build (one-shot)")
    p_build.add_argument("src")
    p_build.add_argument("--base", default="0x00000000")

    args = parser.parse_args()

    if args.cmd == "repl":
        repl()
        return

    if args.cmd == "build":
        build_asm(args.src, args.base)
        print("OK: build terminado")
        return

if __name__ == "__main__":
    main()
