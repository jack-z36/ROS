"""Add deploy/src and common/src to sys.path for config test imports."""

import sys
from pathlib import Path

# deploy/src is the package root for pi05.deploy.*
deploy_src = Path(__file__).resolve().parents[2] / "deploy" / "src"
if str(deploy_src) not in sys.path:
    sys.path.insert(0, str(deploy_src))

# common/src is the package root for pi05.common.*
common_src = Path(__file__).resolve().parents[2] / "common" / "src"
if str(common_src) not in sys.path:
    sys.path.insert(0, str(common_src))
