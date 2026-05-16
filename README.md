# ARM32 Teaching Simulator (TFG)

Simulador docente de ARM32 clasico orientado a ejecucion y depuracion paso a paso.

SO objetivo: Windows con distribucion final autocontenida.
Entorno de desarrollo actual: Windows.

## Estado actual

- Arquitectura objetivo: ARM de 32 bits en modo ARM clasico.
- Backend de ejecucion: Unicorn Engine.
- Toolchain: GNU ARM (`arm-none-eabi-*`).
- Pipeline: `.s -> .o -> .elf -> .bin`.
- CLI interactiva para build, load, step/next/finish, run, registros, memoria, breakpoints, desensamblado y excepciones.
- Soporte docente de excepciones ARM: Reset, Undefined Instruction, SWI/SVC, Prefetch Abort, Data Abort, IRQ y FIQ.
- Motor inicial de ejercicios con validacion de registros y memoria final.
- Correccion por carpeta con `checks.json`, incluyendo excepciones esperadas.

## Arranque por defecto

El entorno de carga sigue el mapa usado en la EPD6:

- direccion de carga por defecto: `0x00010000`;
- vectores ARM copiados a `0x00000000` cuando el binario los contiene;
- modo final tras `load`: usuario;
- pila de usuario: `0x00700000`;
- pilas preparadas para FIQ, IRQ, SVC, ABT, UND, SYS y USER;
- UART MMIO mapeada en `0x101F1000`.

## Comandos principales

```powershell
python -m sim doctor
python -m sim build examples/asm/hello.s
python -m sim check examples/exercises
python -m sim repl
```

Dentro del REPL:

```text
load build/hello.bin
step
next
finish
regs
mem 0x00010000 32
disasm
break bp_here
run
exc
reset
irq
fiq
quit
```

## Dependencias

```powershell
python -m pip install -r requirements.txt
```

## Tests

```powershell
python -m pytest
```

## Entregable Windows

El entregable autocontenido se genera fuera del arbol de desarrollo principal:

```powershell
python -m pip install -r requirements-dev.txt
.\packaging\make_windows_dist.ps1
```

Antes de empaquetar, coloca la toolchain GNU ARM en:

```text
runtime/toolchain/bin/
```

La salida se crea en `packaging/dist/` y no se versiona en Git.

La distribucion final prevista sera autocontenida para Windows, con PyInstaller y toolchain local en `runtime/toolchain/bin`.
