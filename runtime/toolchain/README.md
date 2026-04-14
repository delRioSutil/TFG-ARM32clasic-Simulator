# Toolchain ARM GNU local

Esta carpeta define la ubicacion esperada para la toolchain ARM GNU usada por el simulador en modo autocontenido para Windows.

La estructura esperada es:

```text
runtime/
  toolchain/
    bin/
      arm-none-eabi-as.exe
      arm-none-eabi-ld.exe
      arm-none-eabi-objcopy.exe
      arm-none-eabi-objdump.exe
      arm-none-eabi-nm.exe
```

El simulador busca las herramientas en este orden:

1. Variable de entorno `ARM32SIM_TOOLCHAIN_BIN`.
2. `runtime/toolchain/bin`.
3. `tools/toolchain/bin`.
4. `PATH` del sistema, solo como fallback de desarrollo.

Para comprobar que el entorno esta preparado:

```powershell
python -m sim doctor
```

Notas:

- Los binarios de la toolchain no se incluyen automaticamente en este repositorio.
- Para una entrega autocontenida de Windows, la distribucion final debe incluir esta carpeta `bin` con los ejecutables necesarios.
- El fallback al `PATH` facilita el desarrollo, pero no debe ser el mecanismo principal del entregable final.
