import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

FILENAMES = [
    "01_quickstart.py",
    "02_market_data.py",
    "03_collateral_management.py",
    "04_trading_basics.py",
    "05_position_transfer.py",
]

SCRIPTS = [EXAMPLES_DIR / f for f in FILENAMES]


@pytest.mark.parametrize("script", SCRIPTS, ids=[p.name for p in SCRIPTS])
def test_script_runs(script: Path):
    result = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=30)

    err_msg = f"Script failed with exit code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    assert result.returncode == 0, err_msg
