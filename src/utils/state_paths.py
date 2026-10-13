"""User-owned application state; immutable resources never hold personal data."""
import os
from pathlib import Path


def get_state_root() -> Path:
    explicit = os.environ.get("FILE_MANAGER_HOME") or os.environ.get("CONFIGPATH")
    if explicit:
        return Path(explicit).expanduser().resolve()
    parent = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return parent / "FileManager"
