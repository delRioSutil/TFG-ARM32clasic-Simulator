# Arquitectura objetivo del simulador ARM32 docente

## 1. Proposito del sistema

El proyecto es un simulador/emulador docente de ARM32 orientado a practicas de laboratorio y aprendizaje autonomo. Su objetivo no es reproducir una placa real completa ni un sistema operativo, sino ofrecer un entorno controlado, claro y autocontenido para comprender:

- ejecucion de instrucciones ARM32;
- registros generales y especiales;
- PC, SP, LR y CPSR;
- memoria y pila;
- inspeccion de memoria;
- saltos, llamadas y retorno;
- depuracion paso a paso;
- depuracion tipo debugger: step into, step over y step out;
- breakpoints;
- desensamblado;
- excepciones relevantes del temario;
- ejercicios guiados y validacion de resultados.

La prioridad de diseño es pedagogica: el sistema debe ayudar a entender que ocurre, no solo ejecutar codigo.

## 2. Alcance y limites

El sistema debe ser autocontenido para Windows. En uso normal no debe depender de una placa fisica, WSL, una instalacion global de la toolchain ARM o un Python global configurado manualmente.

El proyecto no persigue:

- emular una placa ARM concreta;
- ejecutar un sistema operativo generalista;
- implementar todos los detalles de ARM de forma industrial;

El alcance aceptable es un modelo docente consistente y explicable, con simplificaciones documentadas cuando sean necesarias.

## 3. Separacion de responsabilidades

### GNU ARM toolchain

La toolchain GNU se encarga de transformar y analizar artefactos:

- `arm-none-eabi-as`: ensambla `.s` a `.o`;
- `arm-none-eabi-ld`: enlaza `.o` a `.elf`;
- `arm-none-eabi-objcopy`: extrae `.bin` plano desde el ELF;
- `arm-none-eabi-objdump`: genera desensamblado legible;
- `arm-none-eabi-nm`: lista simbolos para breakpoints por etiqueta.

La toolchain no ejecuta el programa ni mantiene el estado de CPU.

### Unicorn Engine

Unicorn actua como backend de emulacion:

- crea una CPU ARM32 emulada;
- mapea memoria;
- carga bytes de programa;
- lee y escribe registros;
- ejecuta instrucciones;
- permite hooks para observar ejecucion;
- reporta errores de emulacion.

Unicorn no aporta por si solo una experiencia docente completa, ejercicios, explicaciones ni una interfaz de usuario.

### Codigo propio del proyecto

El codigo propio aporta el valor principal del TFG:

- flujo de uso docente;
- gestion de sesion de depuracion;
- modelo de programa cargado;
- breakpoints;
- visualizacion de registros y memoria;
- desensamblado contextual;
- tratamiento didactico de excepciones;
- ejercicios y validacion;
- mensajes comprensibles;
- empaquetado autocontenido para Windows.

## 4. Pipeline principal

Flujo esperado desde un archivo fuente hasta la ejecucion:

```text
programa.s
  -> ToolchainService.build()
     -> programa.o
     -> programa.elf
     -> programa.bin
     -> simbolos
     -> desensamblado
  -> ProgramArtifact
     -> fuente
     -> ELF
     -> BIN
     -> direccion base
     -> punto de entrada
     -> tabla de simbolos
  -> DebugSession.load()
     -> backend Unicorn
     -> memoria mapeada
     -> PC inicializado
     -> SP inicializado
     -> breakpoints preparados
     -> estado inicial registrado
  -> step/run/debug
     -> registros
     -> memoria
     -> instruccion actual
     -> step into, step over y step out
     -> excepciones
     -> validacion de ejercicios
```

El comando de build no deberia depender de Bash. Para cumplir el objetivo Windows autocontenido, el build debe implementarse en Python invocando ejecutables de toolchain resueltos desde rutas locales del proyecto.

### Arranque y mapa de memoria EPD6

El backend actual inicializa el entorno siguiendo el esquema usado en la EPD6:

- direccion de carga por defecto: `0x00010000`;
- copia inicial de la tabla de vectores desde la imagen cargada a `0x00000000` cuando el binario contiene al menos 32 bytes;
- modo final tras `load`: usuario (`0x10`);
- pila de usuario: `0x00700000`;
- pilas preparadas para FIQ, IRQ, SVC, ABT, UND, SYS y USER segun el mapa de la EPD6;
- pagina MMIO de UART mapeada en `0x101F1000`.

Si existe simbolo `main` en el ELF asociado al binario cargado, `DebugSession.load()` usa esa direccion como punto de entrada. Si no existe, el `PC` inicial queda en la direccion base de carga.

Si existe simbolo `swi_handler` o `svc_handler`, la sesion lo registra como manejador software de excepcion. Esto permite que el backend entre directamente en la rutina docente conocida al producirse `SWI/SVC`, manteniendo a la vez el vector arquitectonico `0x00000008` como dato explicativo del evento.

## 5. Modulos propuestos

```text
sim/
  app/
    cli.py
    commands.py
    messages.py

  core/
    session.py
    program.py
    state.py
    memory.py
    registers.py
    breakpoints.py
    exceptions.py

  backend/
    base.py
    unicorn_backend.py

  toolchain/
    paths.py
    build.py
    gnu.py
    artifacts.py

  debug/
    disassembly.py
    symbols.py
    trace.py

  exercises/
    exercise.py
    loader.py
    validators.py
    results.py

  teaching/
    explanations.py

  config/
    settings.py
```

### `sim.app`

Contiene la interfaz de usuario. En la primera fase sera CLI. Mas adelante puede convivir con GUI. La CLI debe delegar en `DebugSession`; no debe llamar directamente a Unicorn ni a la toolchain.

### `sim.core`

Contiene el modelo del simulador:

- `DebugSession`: coordina programa, backend, breakpoints, excepciones y ejercicios;
- `ProgramArtifact`: describe fuente, ELF, BIN, simbolos, base y punto de entrada;
- `RegisterState`: representa registros de forma legible;
- `MemoryModel`: define regiones de memoria docentes;
- `BreakpointManager`: gestiona breakpoints por direccion y simbolo;
- `ExceptionEvent`: describe excepciones de forma explicable.

### `sim.backend`

Abstrae el motor de ejecucion. `UnicornBackend` sera la implementacion real inicial, pero la CLI no debe depender de Unicorn directamente.

Interfaz minima:

```text
load(program)
reset()
step(count)
run(max_steps)
read_registers()
read_memory(address, size)
write_register(name, value)
add_hook(...)
```

### `sim.toolchain`

Gestiona la toolchain GNU ARM y sus artefactos. Debe resolver rutas locales para favorecer el empaquetado Windows autocontenido.

Responsabilidades:

- localizar ejecutables `arm-none-eabi-*`;
- generar linker script temporal;
- ensamblar;
- enlazar;
- generar binario plano;
- generar simbolos;
- generar desensamblado;
- devolver errores comprensibles.

### `sim.debug`

Agrupa utilidades de depuracion:

- contexto de desensamblado alrededor del PC;
- resolucion de simbolos;
- operaciones de debugger sobre el backend: `step`, `next` y `finish`;
- traza de instrucciones ejecutadas;
- formato docente de instrucciones.

### `sim.exercises`

Define ejercicios y validadores. En el flujo docente previsto, los alumnos trabajan con archivos `.s`; no deben tener que escribir ficheros de configuracion complejos. El profesor debe poder seleccionar una carpeta con ejercicios y definir desde la herramienta los valores esperados al final de cada ejercicio.

Un ejercicio debe poder indicar:

- archivo `.s` del alumno o plantilla de codigo;
- direccion base;
- limite de pasos;
- estado inicial;
- registros esperados al final;
- comprobaciones adicionales opcionales;
- mensajes de ayuda.

Validadores iniciales:

- registro igual a valor esperado;
- memoria igual a valor esperado;
- se alcanza un simbolo;
- ocurre una excepcion concreta;
- no ocurre excepcion;
- el programa termina antes de un limite de pasos;
- opcionalmente, se usa una instruccion concreta.

### `sim.teaching`

Contiene explicaciones asociadas a eventos: que significa PC, por que cambia LR, que implica entrar en SVC, que representa CPSR, etc. Este modulo evita mezclar textos pedagogicos con la logica del backend.

## 6. Modelo de excepciones

Las excepciones deben tratarse como eventos docentes, no solo como errores.

Modelo propuesto:

```text
ExceptionEvent
  type
  address
  vector
  instruction
  immediate
  cpsr_before
  cpsr_after
  lr_value
  mode_before
  mode_after
  explanation
```

### SWI/SVC

Comportamiento docente esperado:

1. Detectar instruccion `swi #imm` o `svc #imm`.
2. Extraer el inmediato.
3. Registrar la direccion de la instruccion.
4. Guardar estado relevante antes de la excepcion.
5. Simular entrada en modo supervisor cuando aplique.
6. Establecer direccion de retorno en LR segun el modelo ARM usado.
7. Saltar al vector de SWI/SVC (`base_vector + 0x08`).
8. Mostrar al alumno que ocurrio y por que.

En la implementacion actual, si el ELF contiene un simbolo `swi_handler` o `svc_handler`, el backend usa esa direccion como destino de ejecucion de la excepcion. Si no existe, el destino queda en el vector `0x00000008`.


### Otras excepciones

Prioridad provisional:

1. SWI/SVC.
2. Undefined instruction.
3. Data abort por acceso invalido de memoria.
4. Prefetch abort por ejecucion fuera de memoria valida.
5. IRQ/FIQ simuladas si el temario lo justifica.

## 7. Ejercicios y correccion

El formato principal de entrada para los alumnos debe ser siempre un archivo `.s`. La correccion no debe exigir que el alumno escriba YAML, JSON u otro formato auxiliar. Si internamente se guarda configuracion, debe entenderse como configuracion del profesor o de la herramienta, no como parte de la entrega del alumno.

Flujo docente previsto:

1. El profesor selecciona una carpeta con ejercicios.
2. La herramienta detecta los archivos `.s` de esa carpeta.
3. El profesor define para cada ejercicio los registros esperados al finalizar la ejecucion, por ejemplo `R0 = 1`, `R1 = 2`, `R2 = 3`, y opcionalmente valores esperados en memoria.
4. La herramienta ensambla y ejecuta cada `.s` en una sesion controlada.
5. La ejecucion se detiene por condicion de fin definida, simbolo final, breakpoint docente o limite de pasos.
6. La herramienta compara automaticamente los registros finales reales con los valores esperados.
7. La herramienta muestra un informe claro de resultados.

Ejemplo conceptual de configuracion interna generada por la herramienta para el profesor:

```text
exercise: suma_basica.s
base: 0x00010000
max_steps: 100
expected_registers:
  R2: 0x00000003
expected_memory:
  - address: 0x00010040
    size: 4
    expected: 0x00000003
```

El motor de ejercicios debe ejecutar el programa en una sesion controlada y producir un resultado claro:

```text
Ejercicio: suma_basica.s
PASS R2 esperado 0x00000003 obtenido 0x00000003
FAIL R3 esperado 0x00000000 obtenido 0x00000005
PASS MEM[0x00010040..0x00010043] esperado 03 00 00 00 obtenido 03 00 00 00
```

La primera version de correccion se centra en registros finales y valores de memoria concretos, porque son comprobaciones simples, defendibles y alineadas con practicas introductorias de ensamblador. Mas adelante se pueden anadir comprobaciones de excepciones esperadas, simbolos alcanzados o flujo ejecutado.

El objetivo no es solo evaluar, sino guiar. Los mensajes deben indicar que registro se esperaba, que valor se obtuvo y, cuando sea posible, que instruccion o zona del programa puede estar relacionada.

## 8. Plan de desarrollo por fases

### Fase 1: documentacion y base autocontenida

- Definir arquitectura objetivo.
- Eliminar dependencia obligatoria de Bash.
- Resolver toolchain desde rutas locales.
- Anadir comando o funcion de diagnostico de entorno.
- Documentar dependencias y empaquetado Windows.

### Fase 2: separacion interna

- Crear `DebugSession`.
- Crear `ProgramArtifact`.
- Crear `BreakpointManager`.
- Crear `ExceptionEvent`.
- Mover la CLI para que use servicios de alto nivel.

### Fase 3: depuracion docente

- Mejorar visualizacion de registros.
- Anadir vista basica de memoria.
- Anadir reset/reload.
- Mejorar desensamblado contextual.
- Mejorar mensajes de error.

### Fase 4: excepciones

- Formalizar SWI/SVC.
- Implementar Undefined instruction.
- Estudiar abortos de memoria.
- Considerar IRQ/FIQ simuladas.

### Fase 5: ejercicios

- Definir formato de ejercicios.
- Implementar loader.
- Implementar validadores basicos.
- Crear practicas de ejemplo.

### Fase 6: GUI

- Crear GUI solo cuando el nucleo CLI sea estable.
- La GUI debe consumir `DebugSession`, no duplicar logica.

## 9. Riesgos principales

- Autocontenido Windows: incluir o localizar la toolchain ARM de forma reproducible puede aumentar tamanyo y complejidad.
- Dependencias Python: Unicorn debe instalarse o empaquetarse de forma controlada.
- Excepciones ARM: el modelo real es complejo; conviene documentar simplificaciones docentes.
- Acoplamiento CLI/backend: debe evitarse para que GUI y ejercicios puedan reutilizar el nucleo.
- Ejercicios demasiado ambiciosos: es preferible empezar con validadores simples y fiables.
- Parsing de herramientas GNU: `objdump` y `nm` generan texto; se debe encapsular el parseo para poder sustituirlo si hace falta.

## 10. Criterio de evolucion

Cada cambio debe poder justificarse con una de estas razones:

- mejora la claridad docente;
- mejora la reproducibilidad;
- reduce acoplamiento;
- facilita ejercicios/correccion;
- mejora robustez;
- prepara el empaquetado autocontenido en Windows.

Si un cambio no ayuda a ninguno de esos puntos, no deberia entrar en el nucleo del TFG.
