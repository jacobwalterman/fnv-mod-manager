from pathlib import Path
import fnv_mod_manager.fs as fs

# paths are from root to file/empty-dir
def collect_file_and_empty_dir_paths(root_dir: Path):
    paths = []
    for dirpath, dirnames, filenames in root_dir.walk(top_down=True, on_error=None, follow_symlinks=False):
        if not filenames and not dirnames:
            paths.append(dirpath)
        for name in filenames:
            paths.append(Path.joinpath(dirpath, name))
    return paths

# symlinks all directory files and dirs onto symlink_tree_root as if symlink_tree_root replaced directory_root
def reroot_directory_tree_into_symlink_tree(directory_root: Path, symlink_tree_root: Path):
    directory_tree_paths = collect_file_and_empty_dir_paths(directory_root)
    for path in directory_tree_paths:
        rerooted_path = create_rerooted_path(path, directory_root, symlink_tree_root)
        create_symlink_make_parent_dirs_no_overwrite(path, rerooted_path)

def create_rerooted_path(path: Path, root_directory: Path, target_root_directory: Path) -> Path:
    return target_root_directory / path.relative_to(root_directory)

def create_symlink_make_parent_dirs_no_overwrite(symlink_source, symlink_destination):
            if not symlink_destination.parent.exists():
                symlink_destination.parent.mkdir(parents=True, exist_ok=True)
            if not symlink_destination.exists():
                symlink_destination.symlink_to(symlink_source)

# writes paths first wins
def merge_mods_first_wins(root_dirs):
    for root_dir in root_dirs:
        reroot_directory_tree_into_symlink_tree(root_dir, fs.SYMLINKED_DATA_PATH)
    reroot_directory_tree_into_symlink_tree(fs.GAME_FILES_PATH, fs.SYMLINKED_GAME_PATH)
