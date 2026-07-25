"""Pytest bootstrap: ensure the package root is importable.

Placing a conftest at the package root makes pytest add this directory to
``sys.path`` so ``import elephant_gripper`` resolves when running the tests
directly (``python3 -m pytest``) without an installed/sourced overlay.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
