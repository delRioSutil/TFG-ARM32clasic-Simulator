# ARM32 Teaching Simulator (TFG)

SO objetivo: Windows (distribución autocontenida).
Entorno de desarrollo: WSL2 Ubuntu (para facilitar toolchain GNU y reproducibilidad).

Objetivo: simulador docente de ARM 32-bit:
- Pipeline GNU: .s -> .elf -> .bin
- Ejecución controlada (step/run), breakpoints, inspección de registros/memoria
- Excepciones: Reset, Undefined, SWI, Prefetch Abort, Data Abort, IRQ, FIQ
- UI: CLI de pruebas primero, GUI definitiva después

Motor de ejecución (por decidir con el tutor): Unicorn vs QEMU.
