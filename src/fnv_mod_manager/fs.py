import os
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    return Path(base) if base else Path.home() / ".local" / "share"


USER_NAME = "myuser"
PACKAGE_NAME = "fnv-mod-manager"


@dataclass(frozen=True)
class Layout:
    program_root: Path
    names_config_path: Path
    load_order_configuration_path: Path
    store_path: Path
    ini_path: Path
    fallout_custom_ini_path: Path
    mods_path: Path
    esps_path: Path
    loose_files_path: Path
    game_files_path: Path
    root_files_path: Path
    temporary_files_path: Path
    prefix_path: Path
    symlinked_ini_path: Path
    symlinked_fallout_custom_ini_path: Path
    hash_manifest_path: Path
    nvse_path: Path
    fallout_new_vegas_path: Path
    symlinked_game_path: Path
    symlinked_data_path: Path


def build_layout(root: Path, user_name: str = USER_NAME) -> Layout:
    store_path = root / "store"
    ini_path = store_path / "ini"
    game_files_path = store_path / "game-files"
    root_files_path = store_path / "root"
    temporary_files_path = store_path / "tmp"
    prefix_path = root / "prefix"
    symlinked_ini_path = (
        prefix_path / user_name / "Documents" / "My Games" / "FalloutNV"
    )
    symlinked_game_path = root / "Fallout New Vegas"
    directories = (
        symlinked_game_path,
        prefix_path,
        temporary_files_path,
        root_files_path,
        store_path,
        ini_path,
        game_files_path,
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    return Layout(
        program_root=root,
        names_config_path=root / "names.toml",
        load_order_configuration_path=root / "configuration.toml",
        store_path=store_path,
        ini_path=ini_path,
        fallout_custom_ini_path=ini_path / "FalloutCustom.ini",
        mods_path=store_path / "mods",
        esps_path=store_path / "esps",
        loose_files_path=store_path / "loose-files",
        game_files_path=game_files_path,
        root_files_path=root_files_path,
        temporary_files_path=temporary_files_path,
        prefix_path=prefix_path,
        symlinked_ini_path=symlinked_ini_path,
        symlinked_fallout_custom_ini_path=symlinked_ini_path / "FalloutCustom.ini",
        hash_manifest_path=temporary_files_path / "hash-manifest",
        nvse_path=root_files_path / "NVSE",
        fallout_new_vegas_path=game_files_path / "Fallout New Vegas",
        symlinked_game_path=symlinked_game_path,
        symlinked_data_path=symlinked_game_path / "Data",
    )


def default_layout() -> Layout:
    return build_layout(data_dir() / PACKAGE_NAME)


def extract_archive(archive_path, dest_dir):
    destination = dest_dir / Path(archive_path).stem
    subprocess.run(
        ["7z", "x", str(archive_path), f"-o{destination}", "-y"],
        check=True,
    )
    return destination


def remove_files_in_temp(temporary_files_path: Path):
    for directory_item in temporary_files_path.iterdir():
        if directory_item.is_dir():
            shutil.rmtree(directory_item)
        else:
            directory_item.unlink()


@contextmanager
def use_temp_dir(temporary_files_path: Path):
    remove_files_in_temp(temporary_files_path)
    try:
        yield temporary_files_path
    finally:
        remove_files_in_temp(temporary_files_path)


@contextmanager
def use_temp_hash_manifest(hash_manifest_path: Path):
    hash_manifest_path.unlink(missing_ok=True)
    try:
        yield hash_manifest_path
    finally:
        hash_manifest_path.unlink(missing_ok=True)
