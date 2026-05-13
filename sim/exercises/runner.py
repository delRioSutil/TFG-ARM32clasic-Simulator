from sim.core.session import DebugSession
from sim.exercises.exercise import CheckResult, Exercise, ExerciseResult
from sim.exercises.validators import (
    validate_expected_exception,
    validate_expected_memory,
    validate_expected_registers,
)


class ExerciseRunner:
    def run(self, exercise: Exercise) -> ExerciseResult:
        session = DebugSession()
        artifacts = session.build(str(exercise.source_path), exercise.base, verbose=False)
        session.load(artifacts["bin"], exercise.base)

        stop_symbol_found = True
        if exercise.stop_symbol is not None:
            stop_symbol_found = self._try_add_stop_breakpoint(session, exercise.stop_symbol)
        run_reason, final_pc = session.run(max_steps=exercise.max_steps)

        checks = []
        if not stop_symbol_found:
            checks.append(
                CheckResult(
                    passed=False,
                    message=f"FAIL simbolo de fin '{exercise.stop_symbol}' no encontrado",
                )
            )

        if run_reason == "max":
            checks.append(
                CheckResult(
                    passed=False,
                    message=f"FAIL ejecucion detenida por max_steps={exercise.max_steps}",
                )
            )
        actual_exception = session.last_exception() if run_reason == "exception" else None
        checks.extend(
            validate_expected_exception(
                actual_exception,
                exercise.expected_exception,
                exercise.allow_unexpected_exceptions,
            )
        )

        checks.extend(validate_expected_registers(session.regs(), exercise.expected_registers))
        checks.extend(validate_expected_memory(session.memory, exercise.expected_memory))

        return ExerciseResult(
            exercise=exercise,
            run_reason=run_reason,
            final_pc=final_pc,
            checks=checks,
        )

    def _try_add_stop_breakpoint(self, session: DebugSession, symbol: str) -> bool:
        try:
            session.add_breakpoint(symbol)
        except ValueError:
            return False
        return True
