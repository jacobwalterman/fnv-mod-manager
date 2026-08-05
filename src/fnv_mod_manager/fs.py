import os
from pathlib import Path 
import subprocess

# TODO: BUGFIX: will potentially overwrite and potentially merge two mods with the same name
def extract_archive(archive_path, dest_dir):
    destination = dest_dir / Path(archive_path).stem
    subprocess.run(
        ["7z", "x", str(archive_path), f"-o{destination}", "-y"],
        check=True,
    )
    return destination

def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    return Path(base) if base else Path.home() / ".local" / "share"

PACKAGE_NAME = "fnv-mod-manager"
PROGRAM_ROOT = data_dir() / PACKAGE_NAME
NAMES_CONFIG_PATH = PROGRAM_ROOT / "names.toml"
LOAD_ORDER_CONFIGURATION_PATH = PROGRAM_ROOT / "configuration.toml"
STORE_PATH = PROGRAM_ROOT / "store"
MODS_PATH =  STORE_PATH / "mods"
ESPS_PATH =  STORE_PATH / "esps"
LOOSE_FILES_PATH =  STORE_PATH / "loose-files"
GAME_FILES_PATH = STORE_PATH / "game-files" 
ROOT_FILES_PATH = STORE_PATH / "root"
NVSE_PATH = ROOT_FILES_PATH / "NVSE"
FALLOUT_NEW_VEGAS_PATH = GAME_FILES_PATH / "Fallout New Vegas"
SYMLINKED_GAME_PATH = PROGRAM_ROOT / "Fallout New Vegas"
SYMLINKED_DATA_PATH = SYMLINKED_GAME_PATH / "Data"
