#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   ./tools/build.sh path/al/programa.s [base_hex]
# Ej:
#   ./tools/build.sh examples/asm/hello.s
#   ./tools/build.sh examples/asm/hello.s 0x00010000

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <archivo.s> [BASE]"
  exit 1
fi

SRC="$1"
BASE="${2:-0x00000000}"

if [[ ! -f "$SRC" ]]; then
  echo "Error: no existe el archivo: $SRC"
  exit 1
fi

# Derivar nombre (sin ruta y sin extensión)
NAME="$(basename "$SRC")"
NAME="${NAME%.s}"

OUTDIR="build"
OBJ="$OUTDIR/$NAME.o"
ELF="$OUTDIR/$NAME.elf"
BIN="$OUTDIR/$NAME.bin"
LDSCRIPT="$OUTDIR/linker_$NAME.ld"

mkdir -p "$OUTDIR"

# Generar linker script (sin editar nada a mano)
cat > "$LDSCRIPT" << LDEOF
ENTRY(_start)

SECTIONS
{
  . = $BASE;
  .text : { *(.text*) }
  .rodata : { *(.rodata*) }
  .data : { *(.data*) }
  .bss : { *(.bss*) *(COMMON) }
}
LDEOF

echo "[1/3] Assembling: $SRC -> $OBJ"
arm-none-eabi-as -o "$OBJ" "$SRC"

echo "[2/3] Linking: $OBJ -> $ELF (BASE=$BASE)"
arm-none-eabi-ld -T "$LDSCRIPT" -o "$ELF" "$OBJ"

echo "[3/3] Objcopy: $ELF -> $BIN"
arm-none-eabi-objcopy -O binary "$ELF" "$BIN"

echo "OK"
echo "  ELF: $ELF"
echo "  BIN: $BIN"
