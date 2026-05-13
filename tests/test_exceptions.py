ARM_MODE_SVC = 0x13
ARM_MODE_ABT = 0x17
ARM_MODE_UND = 0x1B
ARM_MODE_IRQ = 0x12
ARM_MODE_FIQ = 0x11


def _step_many(session, count: int):
    for _ in range(count):
        session.step()


def test_swi_exception_event(loaded_session):
    session, _elf_path, _bin_path = loaded_session("examples/asm/exc_swi.s")

    _step_many(session, 3)
    event = session.last_exception()
    regs = session.regs()

    assert event.type == "SWI"
    assert event.vector == 0x00000008
    assert event.handler == 0x00010044
    assert event.lr == 0x00010028
    assert regs["CPSR"] & 0x1F == ARM_MODE_SVC


def test_undefined_instruction_exception_event(loaded_session):
    session, _elf_path, _bin_path = loaded_session("examples/asm/exc_undef.s")

    session.step()
    event = session.last_exception()

    assert event.type == "UNDEF"
    assert event.vector == 0x00000004
    assert session.regs()["CPSR"] & 0x1F == ARM_MODE_UND


def test_data_abort_exception_event(loaded_session):
    session, _elf_path, _bin_path = loaded_session("examples/asm/exc_data_abort.s")

    _step_many(session, 2)
    event = session.last_exception()

    assert event.type == "DABORT"
    assert event.vector == 0x00000010
    assert event.fault_access == "read"
    assert event.fault_address == 0x09000000
    assert session.regs()["CPSR"] & 0x1F == ARM_MODE_ABT


def test_prefetch_abort_exception_event(loaded_session):
    session, _elf_path, _bin_path = loaded_session("examples/asm/exc_prefetch_abort.s")

    session.step()
    event = session.last_exception()

    assert event.type == "PABORT"
    assert event.vector == 0x0000000C
    assert event.fault_access == "fetch"
    assert event.fault_address == 0x09000000
    assert session.regs()["CPSR"] & 0x1F == ARM_MODE_ABT


def test_simulated_reset_irq_and_fiq(loaded_session):
    session, _elf_path, _bin_path = loaded_session("examples/asm/exc_swi.s")

    session.reset()
    assert session.last_exception().type == "RESET"
    assert session.last_exception().vector == 0x00000000
    assert session.regs()["CPSR"] & 0x1F == ARM_MODE_SVC

    session.irq()
    assert session.last_exception().type == "IRQ"
    assert session.last_exception().vector == 0x00000018
    assert session.regs()["CPSR"] & 0x1F == ARM_MODE_IRQ

    session.fiq()
    assert session.last_exception().type == "FIQ"
    assert session.last_exception().vector == 0x0000001C
    assert session.regs()["CPSR"] & 0x1F == ARM_MODE_FIQ
