"""Add common/src to sys.path for test imports."""

import sys
from pathlib import Path

# common/src is the package root for pi05.common.*
common_src = Path(__file__).resolve().parents[2] / "src"
if str(common_src) not in sys.path:
    sys.path.insert(0, str(common_src))
