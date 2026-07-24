import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "grader" / "scripts"))


collect_ignore = ["quarantine"]


def pytest_configure(config):
    basetemp = REPO_ROOT / ".pytest_tmp"
    basetemp.mkdir(exist_ok=True)
    if not config.option.basetemp:
        config.option.basetemp = str(basetemp)
