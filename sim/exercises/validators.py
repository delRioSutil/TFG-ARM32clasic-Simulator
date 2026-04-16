from sim.exercises.exercise import CheckResult


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
