import os
from pathlib import Path 
import subprocess

PACKAGE_NAME = "fnv-mod-manager"

def extract_archive(archive_path, dest_dir):
    subprocess.run(
        ["7z", "x", str(archive_path), f"-o{dest_dir}", "-y"],
        check=True,
    )

def extract_archive_to_mods_folder(archive_path):
    extract_archive(archive_path, get_mod_manager_mods_folder())

def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    return Path(base) if base else Path.home() / ".local" / "share"

def get_mod_manager_data_folder():
    return data_dir() / PACKAGE_NAME

def get_mod_manager_mods_folder():
    return get_mod_manager_data_folder() / "mods"

####### DEFAULT FOLDER STRUCTURE
root_folder = Path("Fallout New Vegas")
crash_logs = root_folder.joinpath(Path("Crash Logs"))
fallout = root_folder.joinpath(Path("FalloutNV.exe"))
fallout_launcher = root_folder.joinpath(Path("FalloutNVLauncher.exe"))
data = root_folder.joinpath(Path("Data"))
music = data.joinpath(Path("Music"))
shaders = data.joinpath(Path("Shaders"))
sound = data.joinpath(Path("Sound"))
video = data.joinpath(Path("Video"))
