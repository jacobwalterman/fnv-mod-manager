import argparse
import shutil
import subprocess
import sys
from hashlib import sha256
from operator import itemgetter
from pathlib import Path

from tomlkit.toml_file import TOMLFile

import fnv_mod_manager.fs as fs
from fnv_mod_manager.config import get_load_orders
from fnv_mod_manager.esps import set_utimes_in_order
from fnv_mod_manager.fs import extract_archive
from fnv_mod_manager.merge import (
    create_rerooted_path,
    create_symlink_make_parent_dirs_no_overwrite,
    merge_mods_last_wins,
    reroot_directory_tree_into_symlink_tree,
)

CLI_NAME = "fnvmm"


def try_extract_else_exit(filepath: Path, extraction_destination):
    try:
        destination = extract_archive(filepath, extraction_destination)
    except subprocess.CalledProcessError:
        print(f"Error: failed to extract {filepath}", file=sys.stderr)
        sys.exit(1)
    # print(f"Installed {filepath} to {destination}")
    return destination


def reroot_files(file_paths, source_folder, destination_folder):
    for file_path in file_paths:
        symlink_destination = create_rerooted_path(
            file_path, source_folder, destination_folder
        )
        create_symlink_make_parent_dirs_no_overwrite(file_path, symlink_destination)


def append_pretty_name_to_files(pretty_name, mod_name, table_name):
    f = TOMLFile(fs.LOAD_ORDER_CONFIGURATION_PATH)
    load_order_toml = f.read()
    load_order_toml[table_name]["load-order"].append(f"{pretty_name}")
    f.write(load_order_toml)
    f = TOMLFile(fs.NAMES_CONFIG_PATH)
    pretty_names_toml = f.read()
    pretty_names_toml[table_name][pretty_name] = mod_name
    f.write(pretty_names_toml)


def make_hash_manifest_of_directory_contents(
    directory_to_hash_path, hash_manifest_path
):
    file_paths_and_hashes = list()
    for directory_path, subdirectory_names, file_names in directory_to_hash_path.walk():
        for file_name in file_names:
            file_path = directory_path / file_name
            file_hash = get_hex_hash(file_path)
            file_paths_and_hashes.append(
                (file_path.relative_to(directory_path).as_posix(), file_hash)
            )
    file_paths_and_hashes.sort(key=itemgetter(0))
    with open(hash_manifest_path, "w") as f:
        for file_path, file_hash in file_paths_and_hashes:
            f.write(f"{file_path}:{file_hash}\n")


def get_hex_hash(file_path):
    with open(file_path, "rb") as f:
        file_hasher = sha256()
        file_hasher.update(f.read())
    file_hash = file_hasher.hexdigest()
    return file_hash


def get_hash_id_for_directory(directory_path: Path):
    with fs.use_temp_hash_manifest() as hash_manifest_path:
        make_hash_manifest_of_directory_contents(directory_path, hash_manifest_path)
        hash_id = get_hex_hash(hash_manifest_path)
    return hash_id


def install(args):
    filepaths = args.filepaths
    for filepath in filepaths:
        with fs.use_temp_dir() as TEMPORARY_FILES_PATH:
            extracted_mod_temp_directory = try_extract_else_exit(
                filepath, TEMPORARY_FILES_PATH
            )
            mod_name = extracted_mod_temp_directory.name
            hash_id = get_hash_id_for_directory(extracted_mod_temp_directory)
            prospective_mod_path = fs.MODS_PATH / hash_id
            if prospective_mod_path.exists():
                print(
                    f"The path, {prospective_mod_path}, for {mod_name} is occupied! \
                    Unless something has gone wrong, {mod_name} has\
                    been installed previously."
                )
                # go to next mod
                continue
            # TODO: investigate why I couldnt use Path.move_into seems safer
            extracted_mod_directory = extracted_mod_temp_directory.rename(
                prospective_mod_path
            )
        pretty_name = input(f"Pretty name for {mod_name}: ").strip()
        directory_to_search = extracted_mod_directory
        for item in extracted_mod_directory.iterdir():
            if item.is_dir() and item.name.lower() == "data":
                directory_to_search = directory_to_search / item.name
        loose_files = walk_and_collect_loose_files(directory_to_search)
        esps = walk_and_collect_esps(directory_to_search)
        if pretty_name:
            if loose_files:
                append_pretty_name_to_files(pretty_name, hash_id, "loose-files")
            if esps:
                append_pretty_name_to_files(pretty_name, hash_id, "esps")
        reroot_files(loose_files, directory_to_search, fs.LOOSE_FILES_PATH / hash_id)
        reroot_files(esps, directory_to_search, fs.ESPS_PATH / hash_id)


# returns a list of Path objects sorting all files and empty dirs as loose_files
def walk_and_collect_loose_files(mod_dir):
    loose_files = []
    for dir_path, dir_names, file_names in mod_dir.walk():
        if not dir_names and not file_names and dir_path != mod_dir:
            loose_files.append(dir_path)
        for file_name in file_names:
            file_path = dir_path / file_name
            if (
                file_path.suffix.lower() != ".esp"
                and file_path.suffix.lower() != ".esm"
            ):
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
    # clearing old tree for new tree
    if fs.SYMLINKED_GAME_PATH.is_dir():
        shutil.rmtree(fs.SYMLINKED_GAME_PATH)
    merge_mods_last_wins(loose_files)
    set_utimes_in_order(esps)
    for esp in esps:
        print(f"esp to be made: {esp} and place to go: {fs.SYMLINKED_DATA_PATH}")
        reroot_directory_tree_into_symlink_tree(esp, fs.SYMLINKED_DATA_PATH)
        # create_symlink_make_parent_dirs_no_overwrite(esp, fs.SYMLINKED_DATA_PATH)


def build_parser():
    parser = argparse.ArgumentParser(
        prog=CLI_NAME,
        description="Manages fnv mod manager",
        epilog="I care about user issues, so please make a polite report/question "
        "if you have any persistent/unresolved issues! I consider things like "
        'confusion and "stupid mistakes" to be ux issues and I\'m interested '
        "in addressing them, so don't be shy :).",
    )
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="valid subcommands",
        required=True,
    )
    parser_install = subparsers.add_parser(
        "install",
        help="install a file into your mods folder for management",
    )
    parser_install.add_argument(
        "filepaths",
        type=str,
        nargs="+",
        help="the path of the file you want to install into your mods folder.",
    )
    parser_install.set_defaults(func=install)

    parser_create_load_order = subparsers.add_parser(
        "create",
        help="creates your load orders specified in your configuration file",
    )
    parser_create_load_order.set_defaults(func=symlink_load_order)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
