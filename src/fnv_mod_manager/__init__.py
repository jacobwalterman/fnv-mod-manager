"""Symlink-tree merge tool for FNV mod management."""

import pathlib
import os
import time

####### ESP TIMER MODIFICATION
# this is done as FNV loads plugins based on last modified time
def set_utimes_in_order(ordered_plugin_paths):
    base = time.time()
    set_utimes_in_order_with_set_base(base, ordered_plugin_paths)

def set_utimes_in_order_with_set_base(base, ordered_plugin_paths):
    for index, plugin_path in enumerate(ordered_plugin_paths):
        mtime = base + index * 60
        os.utime(plugin_path, times=(mtime, mtime))

__version__ = "0.1.0"
def collect_unique_elements(bucket, unique_elements):
    new_unique_elements = set()
    for element in bucket:
        if element not in unique_elements and element not in new_unique_elements:
            new_unique_elements.add(element)
    return new_unique_elements
# paths are from root to file/empty-dir
def collect_file_and_empty_dir_paths(root_dir: pathlib.Path):
    paths = []
    for dirpath, dirnames, filenames in root_dir.walk(top_down=True, on_error=None, follow_symlinks=False):
        if not filenames and not dirnames:
            paths.append(dirpath)
        for name in filenames:
            paths.append(pathlib.Path.joinpath(dirpath, name))
    return paths

def create_symlink_with_parent_directories(file_source_path, symlink_destination):
    symlink_destination.parent.mkdir(parents=True)
    symlink_destination.symlink_to(file_source_path)

####### LOOSE FILE MOD MERGING DYNAMICS
# this is programmed as first wins instead of last wins
def merge_mods(root_dirs, target_root_directory):
    unique_relative_paths = set()
    for root_dir in root_dirs:
        path_group = (collect_file_and_empty_dir_paths(root_dir))
        orphaned_path_group = [path.relative_to(root_dir) for path in path_group]
        new_unique_relative_paths = collect_unique_elements(orphaned_path_group, unique_relative_paths)
        unique_relative_paths |= new_unique_relative_paths
        for relative_path in new_unique_relative_paths:
            unique_absolute_path = root_dir.joinpath(relative_path)
            symlink_destination = target_root_directory.joinpath(relative_path)
            create_symlink_with_parent_directories(unique_absolute_path, symlink_destination)

if __name__ == "__main__":
    TARGET_ROOT_DIR = pathlib.Path()
    MODLIST = []
    merge_mods(MODLIST, TARGET_ROOT_DIR)
