from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Exercise:
    source_path: Path
    expected_registers: dict[str, int]
    base: str = "0x00010000"
    max_steps: int = 1000
    stop_symbol: str = "end"


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    message: str


@dataclass(frozen=True)
class ExerciseResult:
    exercise: Exercise
    run_reason: str
    final_pc: int
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)
