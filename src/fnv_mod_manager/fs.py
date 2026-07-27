import os
from pathlib import Path 

PACKAGE_NAME = "fnv-mod-manager"

def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    return Path(base) if base else Path.home() / ".local" / "share"

def get_mod_manager_data_folder():
    return data_dir() / PACKAGE_NAME
