import pytest

from fnv_mod_manager.cli import walk_and_collect_loose_files, walk_and_collect_esps

import subprocess
from types import SimpleNamespace

import fnv_mod_manager.cli as cli
import fnv_mod_manager.fs as fs
import pytest

from tomlkit.toml_file import TOMLFile

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


def test_install_uses_data_folder_as_root_when_present(tmp_path, monkeypatch):
    _patch_store_paths(monkeypatch, tmp_path)

    def build(mod_dir):
        (mod_dir).mkdir(parents=True)
        (mod_dir / "readme.txt").write_text("ignore me")
        (mod_dir / "Data" / "Textures").mkdir(parents=True)
        (mod_dir / "Data" / "Textures" / "armor.dds").write_text("fake texture data")
        (mod_dir / "Data" / "plugin.esp").write_text("fake esp data")

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_c", build))
    args = SimpleNamespace(filepaths=[tmp_path / "mod_c.7z"])
    cli.install(args)

    loose_link = fs.LOOSE_FILES_PATH / "mod_c" / "Textures" / "armor.dds"
    esp_link = fs.ESPS_PATH / "mod_c" / "plugin.esp"
    assert loose_link.resolve() == (fs.MODS_PATH / "mod_c" / "Data" / "Textures" / "armor.dds").resolve()
    assert esp_link.resolve() == (fs.MODS_PATH / "mod_c" / "Data" / "plugin.esp").resolve()

    # readme.txt lived outside Data, so it should never get staged
    assert not (fs.LOOSE_FILES_PATH / "mod_c" / "readme.txt").exists()
    # and the "Data" prefix itself shouldn't leak into the staged tree
    assert not (fs.LOOSE_FILES_PATH / "mod_c" / "Data").exists()


@pytest.mark.parametrize("data_name", ["data", "Data", "DATA", "DaTa"])
def test_install_data_folder_case_insensitive(tmp_path, monkeypatch, data_name):
    _patch_store_paths(monkeypatch, tmp_path)

    def build(mod_dir):
        (mod_dir / data_name).mkdir(parents=True)
        (mod_dir / data_name / "plugin.esp").write_text("fake esp data")

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_d", build))
    args = SimpleNamespace(filepaths=[tmp_path / "mod_d.7z"])
    cli.install(args)

    esp_link = fs.ESPS_PATH / "mod_d" / "plugin.esp"
    assert esp_link.resolve() == (fs.MODS_PATH / "mod_d" / data_name / "plugin.esp")


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
 
 
def _patch_config_paths(monkeypatch, tmp_path):
    load_order_path = tmp_path / "configuration.toml"
    names_path = tmp_path / "names.toml"
    load_order_path.write_text(
        '[loose-files]\nload-order = []\n\n[esps]\nload-order = []\n'
    )
    names_path.write_text('[loose-files]\n\n[esps]\n')
    monkeypatch.setattr(fs, "LOAD_ORDER_CONFIGURATION_PATH", load_order_path)
    monkeypatch.setattr(fs, "NAMES_CONFIG_PATH", names_path)
    return load_order_path, names_path
 
 
def _fake_extract_archive_multi(builds):
    """builds: {archive stem -> (mod_name, build_fn)}"""
    def fake(filepath, dest_dir):
        mod_name, build_fn = builds[filepath.stem]
        mod_dir = dest_dir / mod_name
        build_fn(mod_dir)
        return mod_dir
    return fake
 
 
def test_install_prompt_includes_mod_name(tmp_path, monkeypatch):
    _patch_store_paths(monkeypatch, tmp_path)
    _patch_config_paths(monkeypatch, tmp_path)
 
    def build(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")
 
    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_i", build))
 
    seen_prompts = []
    def fake_input(prompt):
        seen_prompts.append(prompt)
        return "Whatever"
    monkeypatch.setattr("builtins.input", fake_input)
 
    args = SimpleNamespace(filepaths=[tmp_path / "mod_i.7z"])
    cli.install(args)
 
    assert "mod_i" in seen_prompts[0]
 
 
def test_install_writes_name_to_loose_files_tables(tmp_path, monkeypatch):
    _patch_store_paths(monkeypatch, tmp_path)
    load_order_path, names_path = _patch_config_paths(monkeypatch, tmp_path)
 
    def build(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")
 
    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_a", build))
    monkeypatch.setattr("builtins.input", lambda prompt: "Pretty Armor Mod")
 
    args = SimpleNamespace(filepaths=[tmp_path / "mod_a.7z"])
    cli.install(args)
 
    load_order = TOMLFile(load_order_path).read()
    names = TOMLFile(names_path).read()
 
    assert "Pretty Armor Mod" in load_order["loose-files"]["load-order"]
    assert names["loose-files"]["Pretty Armor Mod"] == "mod_a"
 
 
def test_install_writes_name_to_esps_table_only(tmp_path, monkeypatch):
    _patch_store_paths(monkeypatch, tmp_path)
    load_order_path, names_path = _patch_config_paths(monkeypatch, tmp_path)
 
    def build(mod_dir):
        mod_dir.mkdir(parents=True)
        (mod_dir / "plugin.esp").write_text("fake esp data")
 
    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_e", build))
    monkeypatch.setattr("builtins.input", lambda prompt: "Pretty Plugin")
 
    args = SimpleNamespace(filepaths=[tmp_path / "mod_e.7z"])
    cli.install(args)
 
    load_order = TOMLFile(load_order_path).read()
    names = TOMLFile(names_path).read()
 
    assert "Pretty Plugin" in load_order["esps"]["load-order"]
    assert names["esps"]["Pretty Plugin"] == "mod_e"
    # shouldn't leak into the other table
    assert "Pretty Plugin" not in load_order["loose-files"]["load-order"]
    assert "loose-files" not in names or "Pretty Plugin" not in names["loose-files"]
 
 
def test_install_writes_name_to_both_tables_when_mod_has_both(tmp_path, monkeypatch):
    _patch_store_paths(monkeypatch, tmp_path)
    load_order_path, names_path = _patch_config_paths(monkeypatch, tmp_path)
 
    def build(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")
        (mod_dir / "plugin.esp").write_text("fake esp data")
 
    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_c", build))
    monkeypatch.setattr("builtins.input", lambda prompt: "Pretty Combo Mod")
 
    args = SimpleNamespace(filepaths=[tmp_path / "mod_c.7z"])
    cli.install(args)
 
    load_order = TOMLFile(load_order_path).read()
    names = TOMLFile(names_path).read()
 
    assert "Pretty Combo Mod" in load_order["loose-files"]["load-order"]
    assert "Pretty Combo Mod" in load_order["esps"]["load-order"]
    assert names["loose-files"]["Pretty Combo Mod"] == "mod_c"
    assert names["esps"]["Pretty Combo Mod"] == "mod_c"
 
 
def test_install_skips_naming_when_input_left_blank(tmp_path, monkeypatch):
    _patch_store_paths(monkeypatch, tmp_path)
    load_order_path, names_path = _patch_config_paths(monkeypatch, tmp_path)
 
    def build(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")
 
    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_f", build))
    monkeypatch.setattr("builtins.input", lambda prompt: "   ")  # blank after strip
 
    args = SimpleNamespace(filepaths=[tmp_path / "mod_f.7z"])
    cli.install(args)
 
    load_order = TOMLFile(load_order_path).read()
    names = TOMLFile(names_path).read()
 
    assert load_order["loose-files"]["load-order"] == []
    assert "loose-files" not in names or len(names["loose-files"]) == 0
 
 
def test_install_prompts_once_per_mod_in_multi_install(tmp_path, monkeypatch):
    _patch_store_paths(monkeypatch, tmp_path)
    load_order_path, names_path = _patch_config_paths(monkeypatch, tmp_path)
 
    def build_g(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")
 
    def build_h(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "weapon.dds").write_text("fake texture data")
 
    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive_multi({
        "mod_g": ("mod_g", build_g),
        "mod_h": ("mod_h", build_h),
    }))
 
    prompts = iter(["Pretty Armor", "Pretty Weapon"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(prompts))
 
    args = SimpleNamespace(filepaths=[tmp_path / "mod_g.7z", tmp_path / "mod_h.7z"])
    cli.install(args)
 
    load_order = TOMLFile(load_order_path).read()
    names = TOMLFile(names_path).read()
 
    assert load_order["loose-files"]["load-order"] == ["Pretty Armor", "Pretty Weapon"]
    assert names["loose-files"]["Pretty Armor"] == "mod_g"
    assert names["loose-files"]["Pretty Weapon"] == "mod_h"
 

