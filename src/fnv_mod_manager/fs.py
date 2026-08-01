import os
from pathlib import Path 
import subprocess

PACKAGE_NAME = "fnv-mod-manager"

# TODO: BUGFIX: will overwrite and potentially merge two mods with the same name
def extract_archive(archive_path, dest_dir):
    destination = dest_dir / Path(archive_path).stem
    subprocess.run(
        ["7z", "x", str(archive_path), f"-o{destination}", "-y"],
        check=True,
    )
    return destination

def extract_archive_to_mods_folder(archive_path):
    return extract_archive(archive_path, get_mod_manager_mods_folder())

def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    return Path(base) if base else Path.home() / ".local" / "share"

def get_mod_manager_data_folder():
    return data_dir() / PACKAGE_NAME

def get_mod_manager_mods_folder():
    return get_mod_manager_data_folder() / "mods"

def get_mod_manager_loose_files_folder():
    return  get_mod_manager_data_folder() / "loose_files"

def get_mod_manager_esps_folder():
    return get_mod_manager_data_folder() / "esps"

def create_default_FNV_folder_structure(destination):
    root_folder = Path("Fallout New Vegas")
    crash_logs = root_folder.joinpath(Path("Crash Logs"))
    data = root_folder.joinpath(Path("Data"))
    music = data.joinpath(Path("Music"))
    shaders = data.joinpath(Path("Shaders"))
    sound = data.joinpath(Path("Sound"))
    video = data.joinpath(Path("Video"))
    # fallout = root_folder.joinpath(Path("FalloutNV.exe"))
    # fallout_launcher = root_folder.joinpath(Path("FalloutNVLauncher.exe"))
    directories = [root_folder, crash_logs, data, music, shaders, sound, video]
    for directory in directories:
        to_make = Path(destination) / directory
        to_make.mkdir(parents=True, exist_ok=True)

