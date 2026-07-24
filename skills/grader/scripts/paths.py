from __future__ import annotations

import os
from pathlib import Path


def grader_home(env=None, home=None) -> Path:
    env = env if env is not None else os.environ
    if env.get("GRADER_HOME"):
        return Path(env["GRADER_HOME"]).expanduser()
    home = home if home is not None else Path.home()
    return home / ".grader"
