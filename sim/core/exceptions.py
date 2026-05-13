from dataclasses import dataclass


@dataclass(frozen=True)
class ExceptionEvent:
    """Describes an exception in a pedagogical, frontend-friendly format."""

    type: str
    pc: int
    vector: int | None = None
    handler: int | None = None
    imm24: int | None = None
    cpsr_before: int | None = None
    cpsr_after: int | None = None
    lr: int | None = None
    fault_address: int | None = None
    fault_access: str | None = None
    explanation: str = ""
