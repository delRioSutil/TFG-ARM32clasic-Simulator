ARM32 Teaching Simulator - Entregable Windows

Uso rapido:

  sim.exe doctor
  sim.exe build examples\asm\hello.s
  sim.exe repl
  sim.exe check examples\exercises

Notas:

- El ejecutable incluye el runtime de Python y las dependencias necesarias.
- La toolchain GNU ARM debe estar incluida en runtime\toolchain\bin dentro de esta carpeta.
- Los programas de los alumnos son archivos .s.
- La correccion por carpeta usa un JSON de profesor, por defecto checks.json.

Comandos principales en modo interactivo:

  load <file.bin>
  step
  next
  finish
  regs
  mem <0xADDR> [size]
  disasm [n]
  break <0xADDR|symbol>
  run [max_steps]
  exc
  quit
