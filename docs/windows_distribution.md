# Distribucion Windows autocontenida

## Estrategia elegida

El proyecto seguira una estrategia de repositorio ligero y paquete final autocontenido.

Esto significa:

- El repositorio de GitHub contiene el codigo fuente, documentacion, ejemplos y estructura de carpetas.
- Los binarios pesados de la toolchain ARM GNU no se versionan en Git.
- La distribucion final para Windows se preparara como un ZIP o release que incluya las dependencias binarias necesarias dentro de `runtime/`.

Esta estrategia evita que el historial de Git crezca con ejecutables grandes, pero permite entregar una herramienta autocontenida al usuario final.

## Estructura esperada del paquete final

```text
TFG-ARM32-Simulator/
  sim/
  examples/
  docs/
  runtime/
    toolchain/
      bin/
        arm-none-eabi-as.exe
        arm-none-eabi-ld.exe
        arm-none-eabi-objcopy.exe
        arm-none-eabi-objdump.exe
        arm-none-eabi-nm.exe
        ...
  README.md
```

El paquete final debe permitir ensamblar programas ARM sin depender de una instalacion global de la toolchain ni del `PATH` del sistema.

## Toolchain ARM GNU

El simulador busca la toolchain en este orden:

1. Variable de entorno `ARM32SIM_TOOLCHAIN_BIN`.
2. `runtime/toolchain/bin`.
3. `tools/toolchain/bin`.
4. `PATH` del sistema, solo como fallback de desarrollo.

Para uso docente y entrega final, el mecanismo principal debe ser `runtime/toolchain/bin`.

## Repositorio frente a distribucion final

### Repositorio GitHub

El repositorio debe incluir:

- codigo Python;
- documentacion;
- ejemplos `.s`;
- estructura vacia `runtime/toolchain/bin/.gitkeep`;
- scripts auxiliares;
- pruebas.

El repositorio no debe incluir por defecto:

- ejecutables grandes de la toolchain;
- binarios generados en `build/`;
- artefactos `.o`, `.elf`, `.bin`;
- entornos virtuales.

### ZIP o release final

El ZIP final debe incluir:

- todo el codigo necesario;
- la carpeta `runtime/toolchain/bin` con ejecutables ARM GNU;
- dependencias Python resueltas o empaquetadas segun la estrategia final;
- instrucciones de ejecucion para Windows;
- ejemplos y ejercicios.

## Comprobacion del entorno

El comando de diagnostico es:

```powershell
python -m sim doctor
```

En una distribucion autocontenida correcta, la salida deberia indicar que las herramientas ARM se encuentran en una ruta local del proyecto, por ejemplo:

```text
OK   arm-none-eabi-as: ...\runtime\toolchain\bin\arm-none-eabi-as.exe (local)
```

Si aparecen como `(PATH)`, el entorno funciona para desarrollo, pero todavia no representa una distribucion completamente autocontenida.

## Justificacion academica

Esta decision mantiene dos objetivos a la vez:

- El desarrollo en GitHub sigue siendo limpio, mantenible y facil de revisar.
- La entrega docente puede ser autocontenida para Windows mediante un paquete final con todas las dependencias necesarias.

La toolchain GNU se mantiene porque aporta un flujo realista y explicable para arquitectura de computadores: ensamblado, enlazado, generacion de binario, simbolos y desensamblado.
