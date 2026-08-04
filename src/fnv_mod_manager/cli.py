import argparse
import subprocess
import sys

import fnv_mod_manager.fs as fs

from fnv_mod_manager.esps import set_utimes_in_order
from fnv_mod_manager.fs import extract_archive 
from fnv_mod_manager.merge import  merge_mods_first_wins, create_symlink_make_parent_dirs_no_overwrite, create_rerooted_path, reroot_directory_tree_into_symlink_tree
from fnv_mod_manager.config import get_load_orders

from pathlib import Path

CLI_NAME = 'fnvmm'

def try_extract_else_exit(filepath: Path):
    try:
        destination = extract_archive(filepath, fs.MODS_PATH)
    except subprocess.CalledProcessError:
        print(f"Error: failed to extract {filepath}", file=sys.stderr)
        sys.exit(1)
    print(f"Installed {filepath} to {destination}")
    return destination

def reroot_files(file_paths, source_folder, destination_folder):
    for file_path in file_paths:
        symlink_destination = create_rerooted_path(file_path, source_folder, destination_folder)
        create_symlink_make_parent_dirs_no_overwrite(file_path, symlink_destination)

# TODO: BUGFIX: the loose_files esps creation should have the same issue of potential accidental merges with mods/ base folders with the same name
def install(args):
    filepaths = args.filepaths
    for filepath in filepaths:
        extracted_mod_directory = try_extract_else_exit(filepath)
        mod_name = extracted_mod_directory.name
        directory_to_search = extracted_mod_directory
        for item in extracted_mod_directory.iterdir():
            if item.is_dir() and item.name.lower() == "data":
                directory_to_search = directory_to_search / item.name

        loose_files = walk_and_collect_loose_files(directory_to_search)
        esps = walk_and_collect_esps(directory_to_search)

        reroot_files(loose_files, directory_to_search, fs.LOOSE_FILES_PATH / mod_name)
        reroot_files(esps, directory_to_search, fs.ESPS_PATH/ mod_name)

# returns a list of Path objects sorting all files and empty dirs as loose_files
def walk_and_collect_loose_files(mod_dir):
    loose_files = []
    for dir_path, dir_names, file_names in mod_dir.walk():
        if not dir_names and not file_names and dir_path != mod_dir:
            loose_files.append(dir_path)
        for file_name in file_names: 
            file_path = dir_path / file_name
            if file_path.suffix.lower() != ".esp" and file_path.suffix.lower() != ".esm":
                loose_files.append(file_path)
    return loose_files

# returns a list of Path objects sorting all files and empty dirs as esps
def walk_and_collect_esps(mod_dir):
    esps = []
    for dir_path, dir_names, file_names in mod_dir.walk():
        for file_name in file_names: 
            file_path = dir_path / file_name
            if file_path.suffix.lower() == ".esp" or file_path.suffix.lower() == ".esm":
                esps.append(file_path)
    return esps

# TODO: add flags to specify destinations, esps-only, dry run, loose_files only
def symlink_load_order(args):
    loose_files, esps = get_load_orders()
    # reverse slice makes our first wins code function like "normal" last wins code ala current mod managers
    print(loose_files, esps)
    merge_mods_first_wins(loose_files[::-1])
    # TODO: confirm this is in the correct order
    set_utimes_in_order(esps)
    for esp in esps:
        print(f"esp to be made: {esp} and place to go: {fs.SYMLINKED_DATA_PATH}")
        reroot_directory_tree_into_symlink_tree(esp, fs.SYMLINKED_DATA_PATH)
        # create_symlink_make_parent_dirs_no_overwrite(esp, fs.SYMLINKED_DATA_PATH)

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
