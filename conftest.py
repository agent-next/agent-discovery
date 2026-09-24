"""Repo-root conftest: make src-layout imports work for any pytest invocation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
