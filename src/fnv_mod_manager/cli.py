import argparse
import subprocess
import sys

from fnv_mod_manager.fs import extract_archive_to_mods_folder, get_mod_manager_mods_folder, get_mod_manager_esps_folder, get_mod_manager_loose_files_folder
from fnv_mod_manager.merge import create_symlink_with_parent_directories
from pathlib import Path

CLI_NAME = 'fnvmm'

# TODO: BUGFIX: the loose_files esps creation should have the same issue of potential accidental merges with mods/ base folders with the same name
def install(args):
    filepath = Path(args.filepath)
    try:
        destination = extract_archive_to_mods_folder(filepath)
    except subprocess.CalledProcessError:
        print(f"Error: failed to extract {filepath}", file=sys.stderr)
        sys.exit(1)
    print(f"Installed {filepath} to {destination}")

    mod_name = destination.name
    loose_files, esps = walk_and_sort_paths(destination)
    for file_path_group, staging_root, file_type in zip(
        [loose_files, esps],
        [get_mod_manager_loose_files_folder(), get_mod_manager_esps_folder()],
        ["loose files", "esps"],
    ):
        for file_path in file_path_group:
            relative_path = file_path.relative_to(destination)
            symlink_destination = staging_root / mod_name / relative_path
            # print(relative_path, symlink_destination)
            create_symlink_with_parent_directories(file_path, symlink_destination)
        print(f"Staged {file_type} under {staging_root / mod_name}")    

# returns a list of Path objects sorting all files and empty dirs as loose_files or esps
def walk_and_sort_paths(mod_dir):
    esps = []
    loose_files = []
    for dir_path, dir_names, file_names in mod_dir.walk():
        if not dir_names and not file_names:
            loose_files.append(dir_path)
        for file_name in file_names: 
            file_path = dir_path / file_name
            if file_path.suffix == ".esp" or file_path.suffix == ".esm":
                esps.append(file_path)
            else:
                loose_files.append(file_path)
    return loose_files, esps

def build_parser():
    parser = argparse.ArgumentParser(
        prog=CLI_NAME,
        description='Manages fnv mod manager',
        epilog='I care about user issues, so please make a polite report/question if you have any '
               'persistent/unresolved issues! I consider things like confusion and "stupid mistakes" '
               'to be ux issues and I\'m interested in addressing them, so don\'t be shy :).',
    )
    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands',
        required=True,
    )
    parser_install = subparsers.add_parser(
        'install',
        help='install a file into your mods folder for management',
    )
    parser_install.add_argument(
        'filepath', type=str,
        help='the path of the file you want to install into your mods folder.',
    )
    parser_install.set_defaults(func=install)
    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
