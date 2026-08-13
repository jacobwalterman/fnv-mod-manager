import os
from pathlib import Path 
import subprocess
import shutil
from contextlib import contextmanager

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
TEMPORARY_FILES_PATH = STORE_PATH / "tmp"
HASH_MANIFEST_PATH = TEMPORARY_FILES_PATH / "hash-manifest"
NVSE_PATH = ROOT_FILES_PATH / "NVSE"
FALLOUT_NEW_VEGAS_PATH = GAME_FILES_PATH / "Fallout New Vegas"
SYMLINKED_GAME_PATH = PROGRAM_ROOT / "Fallout New Vegas"
SYMLINKED_DATA_PATH = SYMLINKED_GAME_PATH / "Data"

def extract_archive(archive_path, dest_dir):
    destination = dest_dir / Path(archive_path).stem
    subprocess.run(
        ["7z", "x", str(archive_path), f"-o{destination}", "-y"],
        check=True,
    )
    return destination

def remove_files_in_temp(temporary_files_path=None):
    if temporary_files_path is None:
        temporary_files_path = TEMPORARY_FILES_PATH
    for directory_item in temporary_files_path.iterdir():
        if directory_item.is_dir():
            shutil.rmtree(directory_item)
        else:
            directory_item.unlink()


@contextmanager
def use_temp_dir(temporary_files_path=None):
    if temporary_files_path is None:
        temporary_files_path = TEMPORARY_FILES_PATH
    remove_files_in_temp(temporary_files_path)
    try:
        yield temporary_files_path
    finally:
        remove_files_in_temp(temporary_files_path)


@contextmanager
def use_temp_hash_manifest(hash_manifest_path=None):
    if hash_manifest_path is None:
        hash_manifest_path = HASH_MANIFEST_PATH
    hash_manifest_path.unlink(missing_ok=True)
    try:
        yield hash_manifest_path
    finally:
        hash_manifest_path.unlink(missing_ok=True)
