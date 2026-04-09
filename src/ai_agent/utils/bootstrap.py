"""Bootstrap helpers for direct script execution."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_src_on_path(file_path: str, parents_to_src: int) -> None:
    """Insert project `src` path into sys.path for direct file execution.

    Args:
        file_path: Usually `__file__`.
        parents_to_src: How many `.parents[]` hops from file to `src`.
    """
    src_path = str(Path(file_path).resolve().parents[parents_to_src])
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

