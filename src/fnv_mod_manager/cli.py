import argparse
import subprocess
import sys

import fnv_mod_manager.fs as fs

from fnv_mod_manager.esps import set_utimes_in_order
from fnv_mod_manager.fs import extract_archive 
from fnv_mod_manager.merge import  merge_mods_first_wins
from fnv_mod_manager.config import get_load_orders

from pathlib import Path

CLI_NAME = 'fnvmm'

def create_symlink_with_parent_directories(file_source_path, symlink_destination):
    if not symlink_destination.parent.exists():
        symlink_destination.parent.mkdir(parents=True, exist_ok=True)
    if not symlink_destination.exists():
        symlink_destination.symlink_to(file_source_path)

# TODO: BUGFIX: the loose_files esps creation should have the same issue of potential accidental merges with mods/ base folders with the same name
def install(args):
    filepaths = args.filepaths
    for filepath in filepaths:
        try:
            destination = extract_archive(filepath, fs.MODS_PATH)
        except subprocess.CalledProcessError:
            print(f"Error: failed to extract {filepath}", file=sys.stderr)
            sys.exit(1)
        print(f"Installed {filepath} to {destination}")
        mod_name = destination.name
        loose_files, esps = walk_and_sort_paths(destination)
        for file_path_group, staging_root, file_type in zip(
            [loose_files, esps],
            [fs.LOOSE_FILES_PATH, fs.ESPS_PATH],
            ["loose files", "esps"],
        ):
            for file_path in file_path_group:
                relative_path = file_path.relative_to(destination)
                symlink_destination = staging_root / mod_name / relative_path
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

# TODO: add flags to specify destinations, esps-only, dry run, loose_files only
# this has blurred responsibilities because it knows merge logic
def symlink_load_order(args):
    loose_files, esps = get_load_orders()
    # reverse slice makes our first wins code function like "normal" last wins code ala current mod managers
    merge_mods_first_wins(loose_files[::-1])
    # TODO: confirm this is in the correct order
    set_utimes_in_order(esps)
    for esp in esps:
        create_symlink_with_parent_directories(esp, fs.SYMLINKED_DATA_PATH)

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
        'filepaths', type=str, nargs="+",
        help='the path of the file you want to install into your mods folder.',
    )
    parser_install.set_defaults(func=install)
    
    parser_create_load_order = subparsers.add_parser(
        'create',
        help='creates your load orders specified in your configuration file',
    )
    parser_create_load_order.set_defaults(func=symlink_load_order)
    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
