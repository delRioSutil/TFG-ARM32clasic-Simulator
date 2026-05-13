from pathlib import Path

from sim.app.cli import run_check
from sim.exercises.exercise import Exercise
from sim.exercises.loader import load_exercises
from sim.exercises.runner import ExerciseRunner


def test_loader_reads_folder_check_config():
    exercises = load_exercises("examples/exercises")

    assert [exercise.source_path.name for exercise in exercises] == [
        "suma.s",
        "mem_store.s",
        "expect_swi.s",
        "expect_dabort.s",
    ]
    assert exercises[2].expected_exception == "SWI"
    assert exercises[2].stop_symbol is None


def test_folder_check_command_passes():
    assert run_check("examples/exercises") == 0


def test_unexpected_exception_fails():
    exercise = Exercise(
        source_path=Path("examples/exercises/expect_dabort.s"),
        expected_registers={},
        stop_symbol=None,
        max_steps=20,
    )

    result = ExerciseRunner().run(exercise)

    assert not result.passed
    assert any("excepcion inesperada DABORT" in check.message for check in result.checks)


def test_expected_exception_passes():
    exercise = Exercise(
        source_path=Path("examples/exercises/expect_dabort.s"),
        expected_registers={},
        expected_exception="DABORT",
        stop_symbol=None,
        max_steps=20,
    )

    result = ExerciseRunner().run(exercise)

    assert result.passed
    assert any("excepcion esperada DABORT obtenida DABORT" in check.message for check in result.checks)
