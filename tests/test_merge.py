import pytest
import fnv_mod_manager.fs as fs
from fnv_mod_manager.merge import collect_file_and_empty_dir_paths, reroot_directory_tree_into_symlink_tree, merge_mods_last_wins


def test_collect_file_and_empty_dir_paths_collects_loose_file_in_root(tmp_path):
    mod = tmp_path / "mod_a"
    mod.mkdir(parents=True)
    (mod / "important.dll").write_text("fake dll data")
    collected = collect_file_and_empty_dir_paths(mod)
    assert set(collected) == {mod / "important.dll"}


def test_collect_file_and_empty_dir_paths_collects_single_file(tmp_path):
    mod = tmp_path / "mod_a"
    (mod / "Textures").mkdir(parents=True)
    (mod / "Textures" / "armor.dds").write_text("fake texture data")
    collected = collect_file_and_empty_dir_paths(mod)
    assert collected == [mod / "Textures" / "armor.dds"]


def test_collect_file_and_empty_dir_paths_collects_empty_directories(tmp_path):
    mod = tmp_path / "mod_a"
    (mod / "Textures").mkdir(parents=True)
    collected = collect_file_and_empty_dir_paths(mod)
    assert collected == [mod / "Textures"]


def test_collect_file_and_empty_dir_paths_on_empty_directory(tmp_path):
    mod = tmp_path / "mod_a"
    mod.mkdir()
    collected = collect_file_and_empty_dir_paths(mod)
    assert collected == []


def test_collect_file_and_empty_dir_paths_raises_on_nonexistent_path(tmp_path):
    mod = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        collect_file_and_empty_dir_paths(mod)


def test_collect_file_and_empty_dir_paths_collects_nested_file(tmp_path):
    mod = tmp_path / "mod_a"
    nested = mod / "Textures" / "Armor" / "Raider"
    nested.mkdir(parents=True)
    (nested / "helmet.dds").write_text("fake texture data")
    collected = collect_file_and_empty_dir_paths(mod)
    assert collected == [nested / "helmet.dds"]


def test_collect_file_and_empty_dir_paths_collects_innermost_nested_empty_dir(tmp_path):
    mod = tmp_path / "mod_a"
    nested_empty = mod / "Textures" / "Armor"
    nested_empty.mkdir(parents=True)
    collected = collect_file_and_empty_dir_paths(mod)
    assert collected == [nested_empty]


def test_collect_file_and_empty_dir_paths_collects_mixed_file_and_empty_dir(tmp_path):
    mod = tmp_path / "mod_a"
    (mod / "Textures").mkdir(parents=True)
    (mod / "Textures" / "armor.dds").write_text("fake texture data")
    (mod / "Sound").mkdir()
    collected = collect_file_and_empty_dir_paths(mod)
    assert set(collected) == {
        mod / "Textures" / "armor.dds",
        mod / "Sound",
    }


def test_reroot_directory_tree_into_symlink_tree_symlinks_single_file(tmp_path):
    source = tmp_path / "mod_a"
    tree = tmp_path / "tree"
    (source / "Textures").mkdir(parents=True)
    original = source / "Textures" / "armor.dds"
    original.write_text("fake texture data")

    reroot_directory_tree_into_symlink_tree(source, tree)

    rerooted = tree / "Textures" / "armor.dds"
    assert rerooted.is_symlink()
    assert rerooted.resolve() == original.resolve()


def test_reroot_directory_tree_into_symlink_tree_symlinks_empty_directory(tmp_path):
    source = tmp_path / "mod_a"
    tree = tmp_path / "tree"
    original = source / "Textures"
    original.mkdir(parents=True)

    reroot_directory_tree_into_symlink_tree(source, tree)

    rerooted = tree / "Textures"
    assert not rerooted.is_symlink()


def test_reroot_directory_tree_into_symlink_tree_preserves_nested_structure(tmp_path):
    source = tmp_path / "mod_a"
    tree = tmp_path / "tree"
    nested = source / "Textures" / "Armor" / "Raider"
    nested.mkdir(parents=True)
    original = nested / "helmet.dds"
    original.write_text("fake texture data")

    reroot_directory_tree_into_symlink_tree(source, tree)

    rerooted = tree / "Textures" / "Armor" / "Raider" / "helmet.dds"
    assert rerooted.is_symlink()
    assert rerooted.resolve() == original.resolve()
    assert not (tree / "Textures").is_symlink()
    assert not (tree / "Textures" / "Armor").is_symlink()
    assert not (tree / "Textures" / "Armor" / "Raider").is_symlink()


def test_reroot_directory_tree_into_symlink_tree_symlinks_multiple_entries(tmp_path):
    source = tmp_path / "mod_a"
    tree = tmp_path / "tree"
    (source / "Textures").mkdir(parents=True)
    (source / "Textures" / "armor.dds").write_text("fake texture data")
    (source / "Sound").mkdir()

    reroot_directory_tree_into_symlink_tree(source, tree)

    file_link = tree / "Textures" / "armor.dds"
    dir_link = tree / "Sound"
    assert file_link.is_symlink()
    assert file_link.resolve() == (source / "Textures" / "armor.dds").resolve()
    assert not dir_link.is_symlink()


def test_reroot_directory_tree_into_symlink_tree_on_empty_source_creates_nothing(tmp_path):
    source = tmp_path / "mod_a"
    tree = tmp_path / "tree"
    source.mkdir()

    reroot_directory_tree_into_symlink_tree(source, tree)

    assert not tree.exists() or list(tree.iterdir()) == []


def test_reroot_directory_tree_into_symlink_tree_doesnt_overwrite_existing_target(tmp_path):
    mod_a = tmp_path / "mod_a"
    mod_b = tmp_path / "mod_b"
    tree = tmp_path / "tree"
    (mod_a / "Textures").mkdir(parents=True)
    (mod_a / "Textures" / "armor.dds").write_text("mod a version")
    (mod_b / "Textures").mkdir(parents=True)
    (mod_b / "Textures" / "armor.dds").write_text("mod b version")

    reroot_directory_tree_into_symlink_tree(mod_a, tree)
    reroot_directory_tree_into_symlink_tree(mod_b, tree)
    assert (tree / "Textures" / "armor.dds").read_text() == "mod a version"


def test_merge_mods_last_wins_does_not_write_into_earlier_mods_store_directory(
    tmp_path, monkeypatch
):
    mod_a = tmp_path / "store" / "mods" / "mod_a"
    mod_b = tmp_path / "store" / "mods" / "mod_b"
    (mod_a / "Textures").mkdir(parents=True)
    (mod_b / "Textures").mkdir(parents=True)
    (mod_b / "Textures" / "armor.dds").write_text("mod b version")

    game_files = tmp_path / "game-files" / "Fallout New Vegas"
    game_files.mkdir(parents=True)
    
    # TODO: add patch for NVSE
    monkeypatch.setattr(fs, "SYMLINKED_DATA_PATH", tmp_path / "tree" / "Data")
    monkeypatch.setattr(fs, "FALLOUT_NEW_VEGAS_PATH", game_files)
    monkeypatch.setattr(fs, "SYMLINKED_GAME_PATH", tmp_path / "tree" / "game")

    merge_mods_last_wins([mod_a, mod_b])

    # mod_a's real store content must be exactly what it was before merging
    # anything else — no new symlinks should ever appear inside it.
    assert list(mod_a.rglob("*")) == [mod_a / "Textures"]
