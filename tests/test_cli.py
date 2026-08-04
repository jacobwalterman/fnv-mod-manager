import pytest

from fnv_mod_manager.cli import walk_and_collect_loose_files, walk_and_collect_esps

import subprocess
from types import SimpleNamespace

import fnv_mod_manager.cli as cli
import fnv_mod_manager.fs as fs


# --- walk_and_collect_loose_files ---

def test_walk_and_collect_loose_files_collects_single_file(tmp_path):
    mod = tmp_path / "mod_a"
    (mod / "Textures").mkdir(parents=True)
    (mod / "Textures" / "armor.dds").write_text("fake texture data")
    collected = walk_and_collect_loose_files(mod)
    assert collected == [mod / "Textures" / "armor.dds"]


def test_walk_and_collect_loose_files_collects_empty_directory(tmp_path):
    mod = tmp_path / "mod_a"
    (mod / "Textures").mkdir(parents=True)
    collected = walk_and_collect_loose_files(mod)
    assert collected == [mod / "Textures"]


def test_walk_and_collect_loose_files_collects_nested_file(tmp_path):
    mod = tmp_path / "mod_a"
    nested = mod / "Textures" / "Armor" / "Raider"
    nested.mkdir(parents=True)
    (nested / "helmet.dds").write_text("fake texture data")
    collected = walk_and_collect_loose_files(mod)
    assert collected == [nested / "helmet.dds"]


def test_walk_and_collect_loose_files_on_empty_mod(tmp_path):
    mod = tmp_path / "mod_a"
    mod.mkdir()
    collected = walk_and_collect_loose_files(mod)
    assert collected == []


def test_walk_and_collect_loose_files_excludes_esp_files(tmp_path):
    mod = tmp_path / "mod_a"
    mod.mkdir()
    (mod / "plugin.esp").write_text("fake esp data")
    collected = walk_and_collect_loose_files(mod)
    assert collected == []


# RED TEST: same root cause, for .esm.
def test_walk_and_collect_loose_files_excludes_esm_files(tmp_path):
    mod = tmp_path / "mod_a"
    mod.mkdir()
    (mod / "master.esm").write_text("fake esm data")
    collected = walk_and_collect_loose_files(mod)
    assert collected == []


# RED TEST: same root cause, in a mixed tree. Currently returns both the
# loose file and the esp instead of just the loose file.
def test_walk_and_collect_loose_files_mixed_loose_file_and_esp(tmp_path):
    mod = tmp_path / "mod_a"
    (mod / "Textures").mkdir(parents=True)
    (mod / "Textures" / "armor.dds").write_text("fake texture data")
    (mod / "plugin.esp").write_text("fake esp data")
    collected = walk_and_collect_loose_files(mod)
    assert collected == [mod / "Textures" / "armor.dds"]


# --- walk_and_collect_esps ---

def test_walk_and_collect_esps_collects_single_esp(tmp_path):
    mod = tmp_path / "mod_a"
    mod.mkdir()
    esp = mod / "plugin.esp"
    esp.write_text("fake esp data")
    collected = walk_and_collect_esps(mod)
    assert collected == [esp]


def test_walk_and_collect_esps_collects_single_esm(tmp_path):
    mod = tmp_path / "mod_a"
    mod.mkdir()
    esm = mod / "master.esm"
    esm.write_text("fake esm data")
    collected = walk_and_collect_esps(mod)
    assert collected == [esm]


def test_walk_and_collect_esps_collects_nested_esp(tmp_path):
    mod = tmp_path / "mod_a"
    nested = mod / "Plugins" / "Optional"
    nested.mkdir(parents=True)
    esp = nested / "plugin.esp"
    esp.write_text("fake esp data")
    collected = walk_and_collect_esps(mod)
    assert collected == [esp]


def test_walk_and_collect_esps_ignores_non_esp_files(tmp_path):
    mod = tmp_path / "mod_a"
    (mod / "Textures").mkdir(parents=True)
    (mod / "Textures" / "armor.dds").write_text("fake texture data")
    collected = walk_and_collect_esps(mod)
    assert collected == []


def test_walk_and_collect_esps_ignores_empty_directories(tmp_path):
    mod = tmp_path / "mod_a"
    (mod / "Textures").mkdir(parents=True)
    collected = walk_and_collect_esps(mod)
    assert collected == []


def test_walk_and_collect_esps_mixed_loose_file_and_esp(tmp_path):
    mod = tmp_path / "mod_a"
    (mod / "Textures").mkdir(parents=True)
    (mod / "Textures" / "armor.dds").write_text("fake texture data")
    esp = mod / "plugin.esp"
    esp.write_text("fake esp data")
    collected = walk_and_collect_esps(mod)
    assert collected == [esp]


# ASSUMPTION: suffix matching is case-sensitive as written, so an archive
# shipping "Plugin.ESP" would currently be missed and fall through to
# loose_files instead. If suffixes get normalized before this point (per
# your case-normalization design elsewhere), this test is moot, delete it.
# Otherwise it's a second real gap worth deciding on.
def test_walk_and_collect_esps_collects_uppercase_extension(tmp_path):
    mod = tmp_path / "mod_a"
    mod.mkdir()
    esp = mod / "plugin.ESP"
    esp.write_text("fake esp data")
    collected = walk_and_collect_esps(mod)
    assert collected == [esp]


# --- reroot_files ---

def test_reroot_files_symlinks_single_file(tmp_path):
    source = tmp_path / "mod_a"
    dest = tmp_path / "staged"
    (source / "Textures").mkdir(parents=True)
    original = source / "Textures" / "armor.dds"
    original.write_text("fake texture data")

    cli.reroot_files([original], source, dest)

    rerooted = dest / "Textures" / "armor.dds"
    assert rerooted.is_symlink()
    assert rerooted.resolve() == original.resolve()


def test_reroot_files_creates_real_directory_for_empty_dir_leaf(tmp_path):
    source = tmp_path / "mod_a"
    dest = tmp_path / "staged"
    original = source / "Sound"
    original.mkdir(parents=True)

    cli.reroot_files([original], source, dest)

    rerooted = dest / "Sound"
    assert rerooted.is_dir()
    assert not rerooted.is_symlink()


def test_reroot_files_handles_multiple_paths(tmp_path):
    source = tmp_path / "mod_a"
    dest = tmp_path / "staged"
    (source / "Textures").mkdir(parents=True)
    file_a = source / "Textures" / "armor.dds"
    file_a.write_text("fake texture data")
    file_b = source / "plugin.esp"
    file_b.write_text("fake esp data")

    cli.reroot_files([file_a, file_b], source, dest)

    assert (dest / "Textures" / "armor.dds").resolve() == file_a.resolve()
    assert (dest / "plugin.esp").resolve() == file_b.resolve()


def test_reroot_files_does_not_overwrite_existing_destination(tmp_path):
    source = tmp_path / "mod_a"
    dest = tmp_path / "staged"
    (source / "Textures").mkdir(parents=True)
    original = source / "Textures" / "armor.dds"
    original.write_text("first version")

    cli.reroot_files([original], source, dest)
    first_target = (dest / "Textures" / "armor.dds").resolve()

    other_source = tmp_path / "mod_b" / "Textures" / "armor.dds"
    other_source.parent.mkdir(parents=True)
    other_source.write_text("second version")

    cli.reroot_files([other_source], other_source.parent.parent, dest)

    assert (dest / "Textures" / "armor.dds").resolve() == first_target


# --- install ---

def _fake_extract_archive(mod_name, build_fn):
    def fake(filepath, dest_dir):
        mod_dir = dest_dir / mod_name
        build_fn(mod_dir)
        return mod_dir
    return fake


def _patch_store_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(fs, "MODS_PATH", tmp_path / "store" / "mods")
    monkeypatch.setattr(fs, "LOOSE_FILES_PATH", tmp_path / "store" / "loose-files")
    monkeypatch.setattr(fs, "ESPS_PATH", tmp_path / "store" / "esps")


def test_install_stages_loose_files_and_esps_separately(tmp_path, monkeypatch):
    _patch_store_paths(monkeypatch, tmp_path)

    def build(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")
        (mod_dir / "plugin.esp").write_text("fake esp data")

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_a", build))

    args = SimpleNamespace(filepaths=[tmp_path / "mod_a.7z"])
    cli.install(args)

    loose_link = fs.LOOSE_FILES_PATH / "mod_a" / "Textures" / "armor.dds"
    esp_link = fs.ESPS_PATH / "mod_a" / "plugin.esp"

    assert loose_link.resolve() == (fs.MODS_PATH / "mod_a" / "Textures" / "armor.dds").resolve()
    assert esp_link.resolve() == (fs.MODS_PATH / "mod_a" / "plugin.esp").resolve()
    # esp must not also be staged as a loose file
    assert not (fs.LOOSE_FILES_PATH / "mod_a" / "plugin.esp").exists()


def test_install_stages_empty_directory_as_real_directory(tmp_path, monkeypatch):
    _patch_store_paths(monkeypatch, tmp_path)

    def build(mod_dir):
        (mod_dir / "Sound").mkdir(parents=True)

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_b", build))

    args = SimpleNamespace(filepaths=[tmp_path / "mod_b.7z"])
    cli.install(args)

    staged = fs.LOOSE_FILES_PATH / "mod_b" / "Sound"
    assert staged.is_dir()
    assert not staged.is_symlink()


def test_install_exits_and_stages_nothing_if_extraction_fails(tmp_path, monkeypatch):
    _patch_store_paths(monkeypatch, tmp_path)

    def fake_extract_archive(filepath, dest_dir):
        raise subprocess.CalledProcessError(returncode=2, cmd=["7z"])

    monkeypatch.setattr(cli, "extract_archive", fake_extract_archive)

    args = SimpleNamespace(filepaths=[tmp_path / "bad_mod.7z"])
    with pytest.raises(SystemExit):
        cli.install(args)

    assert not fs.LOOSE_FILES_PATH.exists()
    assert not fs.ESPS_PATH.exists()
