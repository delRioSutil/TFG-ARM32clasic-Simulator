def test_memory_read_reflects_store_instruction(loaded_session, symbol):
    session, elf_path, _bin_path = loaded_session("examples/exercises/mem_store.s")
    value_addr = symbol(elf_path, "value")

    assert session.memory(value_addr, 4) == bytes.fromhex("00000000")

    reason, _pc = session.run(max_steps=20)

    assert reason == "max" or reason == "break"
    assert session.memory(value_addr, 4) == bytes.fromhex("78563412")
