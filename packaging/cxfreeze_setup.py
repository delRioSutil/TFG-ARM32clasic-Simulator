from cx_Freeze import Executable, setup
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


build_exe_options = {
    "packages": ["sim", "unicorn"],
    "include_files": [],
    "excludes": ["tkinter"],
}


setup(
    name="ARM32TeachingSimulator",
    version="0.1.0",
    description="Simulador docente ARM32",
    options={"build_exe": build_exe_options},
    executables=[Executable(str(PROJECT_ROOT / "sim" / "__main__.py"), target_name="sim.exe")],
)
