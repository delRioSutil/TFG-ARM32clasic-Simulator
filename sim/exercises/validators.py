from sim.exercises.exercise import CheckResult
from sim.exercises.exercise import MemoryExpectation


def validate_expected_registers(
    actual_registers: dict[str, int],
    expected_registers: dict[str, int],
) -> list[CheckResult]:
    results = []

    for register, expected in expected_registers.items():
        normalized = register.upper()
        if normalized not in actual_registers:
            results.append(
                CheckResult(
                    passed=False,
                    message=f"FAIL {normalized} no existe en el estado de registros",
                )
            )
            continue

        actual = actual_registers[normalized]
        passed = actual == expected
        status = "PASS" if passed else "FAIL"
        results.append(
            CheckResult(
                passed=passed,
                message=(
                    f"{status} {normalized} esperado 0x{expected:08X} "
                    f"obtenido 0x{actual:08X}"
                ),
            )
        )

    return results


def validate_expected_memory(
    read_memory,
    expected_memory: list[MemoryExpectation],
) -> list[CheckResult]:
    results = []

    for item in expected_memory:
        expected = _expected_to_bytes(item)
        actual = read_memory(item.address, len(expected))
        passed = actual == expected
        status = "PASS" if passed else "FAIL"
        results.append(
            CheckResult(
                passed=passed,
                message=(
                    f"{status} MEM[0x{item.address:08X}..0x{item.address + len(expected) - 1:08X}] "
                    f"esperado {expected.hex(' ').upper()} obtenido {actual.hex(' ').upper()}"
                ),
            )
        )

    return results


def _expected_to_bytes(item: MemoryExpectation) -> bytes:
    expected = item.expected

    if isinstance(expected, bytes):
        return expected

    if isinstance(expected, int):
        return expected.to_bytes(item.size, item.byteorder)

    if isinstance(expected, str):
        text = expected.strip().replace(" ", "")
        if text.startswith(("0x", "0X")):
            text = text[2:]
        if len(text) % 2 != 0:
            text = "0" + text
        return bytes.fromhex(text)

    raise TypeError(f"Valor de memoria esperado no soportado: {type(expected).__name__}")
