import subprocess
from fnv_mod_manager.fs import get_mod_manager_data_folder

def extract_archive(archive_path, dest_dir):
    subprocess.run(
        ["7z", "x", str(archive_path), f"-o{dest_dir}", "-y"],
        check=True,
    )

def extract_archive_to_data_folder(archive_path):
    extract_archive(archive_path, get_mod_manager_data_folder())

