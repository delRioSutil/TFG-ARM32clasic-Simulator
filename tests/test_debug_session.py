ARM_MODE_USER = 0x10


def test_load_initializes_epd6_user_context(loaded_session):
    session, _elf_path, _bin_path = loaded_session("examples/asm/debug_call.s")

    regs = session.regs()

    assert regs["PC"] == 0x00010004
    assert regs["SP"] == 0x00700000
    assert regs["CPSR"] & 0x1F == ARM_MODE_USER


def test_step_enters_function_and_next_steps_over_call(loaded_session):
    step_session, _elf_path, _bin_path = loaded_session("examples/asm/debug_call.s")
    next_session, _elf_path, _bin_path = loaded_session("examples/asm/debug_call.s")

    assert step_session.step() == 0x00010008
    assert step_session.step() == 0x00010014

    assert next_session.step() == 0x00010008
    reason, pc = next_session.next()

    assert reason == "break"
    assert pc == 0x0001000C
    assert next_session.regs()["R0"] == 3


def test_finish_runs_until_lr(loaded_session):
    session, _elf_path, _bin_path = loaded_session("examples/asm/debug_call.s")

    session.step()
    session.step()
    reason, pc = session.finish()

    assert reason == "break"
    assert pc == 0x0001000C
    assert session.regs()["R0"] == 3
