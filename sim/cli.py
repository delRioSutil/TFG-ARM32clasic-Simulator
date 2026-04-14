import argparse
import shlex

from sim.core.toolchain import TOOLCHAIN_ENV, build_asm, toolchain_status
from pathlib import Path
from sim.core.symbols import resolve_symbol
from sim.core.disasm import disasm_around_pc

HELP = """
Comandos:
  build <file.s> [--base 0x00000000]
  load <file.bin> [--base 0x00000000]
  step [n]
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
    from sim.core.backend_unicorn import UnicornBackend

    backend = UnicornBackend()
    current_elf = None
    current_bin = None
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
                name = Path(a.src).stem   # "hello" a partir de ".../hello.s"
                current_elf = f"build/{name}.elf"
                current_bin = f"build/{name}.bin"
                print(f"ELF: {current_elf}")
                print(f"BIN: {current_bin}")
                print("OK: build terminado")

            elif cmd == "doctor":
                print_doctor()

            elif cmd == "load":
                p = argparse.ArgumentParser(prog="load", add_help=False)
                p.add_argument("bin")
                p.add_argument("--base", default="0x00000000")
                a = p.parse_args(parts[1:])
                backend.load_bin(a.bin, a.base)
                current_bin = a.bin
                # Si el bin es build/X.bin, probamos build/X.elf
                if a.bin.endswith(".bin"):
                    guess = a.bin[:-4] + ".elf"
                    if Path(guess).exists():
                        current_elf = guess
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
            
            elif cmd == "break":
                if len(parts) != 2:
                    raise ValueError("Uso: break 0xADDR | break <symbol>")
                target = parts[1]
                if target.startswith("0x") or target.startswith("0X"):
                    backend.add_breakpoint(target)
                    print(f"OK: breakpoint en {target}")
                else:
                    if current_elf is None:
                        raise ValueError("No hay ELF asociado. Ejecuta primero 'build ...' o carga un .bin que tenga .elf al lado.")
                    addr = resolve_symbol(current_elf, target)
                    backend.add_breakpoint(hex(addr))
                    print(f"OK: breakpoint en {target} (0x{addr:08X})")

            elif cmd == "bl":
                bps = sorted(list(backend.breakpoints))
                if not bps:
                    print("(sin breakpoints)")
                else:
                    for a in bps:
                        print(f"* 0x{a:08X}")

            elif cmd == "run":
                max_steps = int(parts[1]) if len(parts) >= 2 else 100000
                reason = backend.run_until_break(max_steps=max_steps)
                pc = backend.regs()["PC"]
                print(f"OK: run terminado ({reason}) PC=0x{pc:08X}")

            elif cmd == "disasm":
                if current_elf is None:
                    raise ValueError("No hay ELF asociado. Ejecuta 'build ...' primero.")
                ctx = 5
                if len(parts) >= 2:
                    ctx = int(parts[1])
                pc = backend.regs()["PC"]
                out_lines = disasm_around_pc(current_elf, pc, context=ctx)
                for l in out_lines:
                    print(l)

            elif cmd == "exc":
                if backend.last_exception is None:
                    print("(no exception)")
                else:
                    e = backend.last_exception
                    if e["type"] == "SWI":
                        print(f'EXC SWI at PC=0x{e["pc"]:08X} imm=0x{e["imm24"]:06X} vector=0x{e["vector"]:08X}')
                    else:
                        print(f'EXC {e["type"]} at PC=0x{e["pc"]:08X}')

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
    p_build.add_argument("--base", default="0x00000000")

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
