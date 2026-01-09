"""VibeForge API - Local UI API for session orchestration."""

from pathlib import Path
import sys

__version__ = "0.1.0"

_REPO_ROOT = Path(__file__).resolve().parents[3]
# Ensure repo-root packages (e.g., models/) are importable when running from apps/api.
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
