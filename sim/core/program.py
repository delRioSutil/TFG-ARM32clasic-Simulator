from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProgramArtifact:
    """Describes the program artifacts associated with a debug session."""

    bin_path: Path
    base: int
    source_path: Path | None = None
    elf_path: Path | None = None

    @classmethod
    def from_source(cls, source: str, base: int, build_dir: Path) -> "ProgramArtifact":
        source_path = Path(source)
        name = source_path.stem
        return cls(
            source_path=source_path,
            bin_path=build_dir / f"{name}.bin",
            elf_path=build_dir / f"{name}.elf",
            base=base,
        )

    @classmethod
    def from_binary(cls, bin_path: str, base: int) -> "ProgramArtifact":
        binary = Path(bin_path)
        elf_path = None

        if binary.suffix == ".bin":
            candidate = binary.with_suffix(".elf")
            if candidate.exists():
                elf_path = candidate

        return cls(
            bin_path=binary,
            elf_path=elf_path,
            base=base,
        )

    def as_cli_artifacts(self) -> dict[str, str]:
        artifacts = {"bin": str(self.bin_path)}
        if self.elf_path is not None:
            artifacts["elf"] = str(self.elf_path)
        return artifacts
