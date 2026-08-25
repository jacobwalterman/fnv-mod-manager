import subprocess
from types import SimpleNamespace

import pytest
from tomlkit.toml_file import TOMLFile

import fnv_mod_manager.cli as cli
import fnv_mod_manager.fs as fs
from fnv_mod_manager.cli import walk_and_collect_esps, walk_and_collect_loose_files

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
#
# ASSUMPTION: cli.install(args, layout) — adjust call sites below if your
# actual signature differs (e.g. keyword arg, different position).


def _fake_extract_archive(mod_name, build_fn):
    def fake(filepath, dest_dir):
        mod_dir = dest_dir / mod_name
        build_fn(mod_dir)
        return mod_dir

    return fake


def _fake_extract_archive_multi(builds):
    """builds: {archive stem -> (mod_name, build_fn)}"""

    def fake(filepath, dest_dir):
        mod_name, build_fn = builds[filepath.stem]
        mod_dir = dest_dir / mod_name
        build_fn(mod_dir)
        return mod_dir

    return fake


def _build_test_layout(tmp_path):
    layout = fs.build_layout(tmp_path)
    layout.mods_path.mkdir(parents=True, exist_ok=True)
    layout.loose_files_path.mkdir(parents=True, exist_ok=True)
    layout.esps_path.mkdir(parents=True, exist_ok=True)
    layout.temporary_files_path.mkdir(parents=True, exist_ok=True)
    return layout


def _write_config_files(layout):
    layout.load_order_configuration_path.write_text(
        "[loose-files]\nload-order = []\n\n[esps]\nload-order = []\n"
    )
    layout.names_config_path.write_text("[loose-files]\n\n[esps]\n")


def _only_installed_hash_id(mods_path):
    installed = list(mods_path.iterdir())
    assert len(installed) == 1, (
        f"expected exactly one installed mod, found {[p.name for p in installed]}"
    )
    return installed[0].name


def test_install_uses_data_folder_as_root_when_present(tmp_path, monkeypatch):
    layout = _build_test_layout(tmp_path)

    def build(mod_dir):
        (mod_dir).mkdir(parents=True)
        (mod_dir / "readme.txt").write_text("ignore me")
        (mod_dir / "Data" / "Textures").mkdir(parents=True)
        (mod_dir / "Data" / "Textures" / "armor.dds").write_text("fake texture data")
        (mod_dir / "Data" / "plugin.esp").write_text("fake esp data")

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_c", build))
    args = SimpleNamespace(filepaths=[tmp_path / "mod_c.7z"])
    cli.install(args, layout)

    hash_id = _only_installed_hash_id(layout.mods_path)
    loose_link = layout.loose_files_path / hash_id / "Textures" / "armor.dds"
    esp_link = layout.esps_path / hash_id / "plugin.esp"
    assert (
        loose_link.resolve()
        == (layout.mods_path / hash_id / "Data" / "Textures" / "armor.dds").resolve()
    )
    assert (
        esp_link.resolve()
        == (layout.mods_path / hash_id / "Data" / "plugin.esp").resolve()
    )
    assert not (layout.loose_files_path / hash_id / "readme.txt").exists()
    assert not (layout.loose_files_path / hash_id / "Data").exists()


@pytest.mark.parametrize("data_name", ["data", "Data", "DATA", "DaTa"])
def test_install_data_folder_case_insensitive(tmp_path, monkeypatch, data_name):
    layout = _build_test_layout(tmp_path)

    def build(mod_dir):
        (mod_dir / data_name).mkdir(parents=True)
        (mod_dir / data_name / "plugin.esp").write_text("fake esp data")

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_d", build))
    args = SimpleNamespace(filepaths=[tmp_path / "mod_d.7z"])
    cli.install(args, layout)

    hash_id = _only_installed_hash_id(layout.mods_path)
    esp_link = layout.esps_path / hash_id / "plugin.esp"
    assert (
        esp_link.resolve()
        == (layout.mods_path / hash_id / data_name / "plugin.esp").resolve()
    )


def test_install_stages_loose_files_and_esps_separately(tmp_path, monkeypatch):
    layout = _build_test_layout(tmp_path)

    def build(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")
        (mod_dir / "plugin.esp").write_text("fake esp data")

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_a", build))
    args = SimpleNamespace(filepaths=[tmp_path / "mod_a.7z"])
    cli.install(args, layout)

    hash_id = _only_installed_hash_id(layout.mods_path)
    loose_link = layout.loose_files_path / hash_id / "Textures" / "armor.dds"
    esp_link = layout.esps_path / hash_id / "plugin.esp"
    assert (
        loose_link.resolve()
        == (layout.mods_path / hash_id / "Textures" / "armor.dds").resolve()
    )
    assert esp_link.resolve() == (layout.mods_path / hash_id / "plugin.esp").resolve()
    assert not (layout.loose_files_path / hash_id / "plugin.esp").exists()


def test_install_stages_empty_directory_as_real_directory(tmp_path, monkeypatch):
    layout = _build_test_layout(tmp_path)

    def build(mod_dir):
        (mod_dir / "Sound").mkdir(parents=True)

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_b", build))
    args = SimpleNamespace(filepaths=[tmp_path / "mod_b.7z"])
    cli.install(args, layout)

    hash_id = _only_installed_hash_id(layout.mods_path)
    staged = layout.loose_files_path / hash_id / "Sound"
    assert staged.is_dir()
    assert not staged.is_symlink()


def test_install_exits_and_stages_nothing_if_extraction_fails(tmp_path, monkeypatch):
    layout = _build_test_layout(tmp_path)

    def fake_extract_archive(filepath, dest_dir):
        raise subprocess.CalledProcessError(returncode=2, cmd=["7z"])

    monkeypatch.setattr(cli, "extract_archive", fake_extract_archive)

    args = SimpleNamespace(filepaths=[tmp_path / "bad_mod.7z"])
    with pytest.raises(SystemExit):
        cli.install(args, layout)

    assert list(layout.mods_path.iterdir()) == []
    assert list(layout.loose_files_path.iterdir()) == []
    assert list(layout.esps_path.iterdir()) == []


def test_install_prompt_includes_mod_name(tmp_path, monkeypatch):
    layout = _build_test_layout(tmp_path)
    _write_config_files(layout)

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
    cli.install(args, layout)

    assert "mod_i" in seen_prompts[0]


def test_install_writes_name_to_loose_files_tables(tmp_path, monkeypatch):
    layout = _build_test_layout(tmp_path)
    _write_config_files(layout)

    def build(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_a", build))
    monkeypatch.setattr("builtins.input", lambda prompt: "Pretty Armor Mod")

    args = SimpleNamespace(filepaths=[tmp_path / "mod_a.7z"])
    cli.install(args, layout)

    hash_id = _only_installed_hash_id(layout.mods_path)
    load_order = TOMLFile(layout.load_order_configuration_path).read()
    names = TOMLFile(layout.names_config_path).read()

    assert "Pretty Armor Mod" in load_order["loose-files"]["load-order"]
    assert names["loose-files"]["Pretty Armor Mod"] == hash_id


def test_install_writes_name_to_esps_table_only(tmp_path, monkeypatch):
    layout = _build_test_layout(tmp_path)
    _write_config_files(layout)

    def build(mod_dir):
        mod_dir.mkdir(parents=True)
        (mod_dir / "plugin.esp").write_text("fake esp data")

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_e", build))
    monkeypatch.setattr("builtins.input", lambda prompt: "Pretty Plugin")

    args = SimpleNamespace(filepaths=[tmp_path / "mod_e.7z"])
    cli.install(args, layout)

    hash_id = _only_installed_hash_id(layout.mods_path)
    load_order = TOMLFile(layout.load_order_configuration_path).read()
    names = TOMLFile(layout.names_config_path).read()

    assert "Pretty Plugin" in load_order["esps"]["load-order"]
    assert names["esps"]["Pretty Plugin"] == hash_id
    assert "Pretty Plugin" not in load_order["loose-files"]["load-order"]
    assert "loose-files" not in names or "Pretty Plugin" not in names["loose-files"]


def test_install_writes_name_to_both_tables_when_mod_has_both(tmp_path, monkeypatch):
    layout = _build_test_layout(tmp_path)
    _write_config_files(layout)

    def build(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")
        (mod_dir / "plugin.esp").write_text("fake esp data")

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_c", build))
    monkeypatch.setattr("builtins.input", lambda prompt: "Pretty Combo Mod")

    args = SimpleNamespace(filepaths=[tmp_path / "mod_c.7z"])
    cli.install(args, layout)

    hash_id = _only_installed_hash_id(layout.mods_path)
    load_order = TOMLFile(layout.load_order_configuration_path).read()
    names = TOMLFile(layout.names_config_path).read()

    assert "Pretty Combo Mod" in load_order["loose-files"]["load-order"]
    assert "Pretty Combo Mod" in load_order["esps"]["load-order"]
    assert names["loose-files"]["Pretty Combo Mod"] == hash_id
    assert names["esps"]["Pretty Combo Mod"] == hash_id


def test_install_skips_naming_when_input_left_blank(tmp_path, monkeypatch):
    layout = _build_test_layout(tmp_path)
    _write_config_files(layout)

    def build(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")

    monkeypatch.setattr(cli, "extract_archive", _fake_extract_archive("mod_f", build))
    monkeypatch.setattr("builtins.input", lambda prompt: "   ")  # blank after strip

    args = SimpleNamespace(filepaths=[tmp_path / "mod_f.7z"])
    cli.install(args, layout)

    load_order = TOMLFile(layout.load_order_configuration_path).read()
    names = TOMLFile(layout.names_config_path).read()

    assert load_order["loose-files"]["load-order"] == []
    assert "loose-files" not in names or len(names["loose-files"]) == 0


def test_install_prompts_once_per_mod_in_multi_install(tmp_path, monkeypatch):
    layout = _build_test_layout(tmp_path)
    _write_config_files(layout)

    def build_g(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "armor.dds").write_text("fake texture data")

    def build_h(mod_dir):
        (mod_dir / "Textures").mkdir(parents=True)
        (mod_dir / "Textures" / "weapon.dds").write_text("fake texture data")

    monkeypatch.setattr(
        cli,
        "extract_archive",
        _fake_extract_archive_multi(
            {
                "mod_g": ("mod_g", build_g),
                "mod_h": ("mod_h", build_h),
            }
        ),
    )

    prompts = iter(["Pretty Armor", "Pretty Weapon"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(prompts))

    args = SimpleNamespace(filepaths=[tmp_path / "mod_g.7z", tmp_path / "mod_h.7z"])
    cli.install(args, layout)

    load_order = TOMLFile(layout.load_order_configuration_path).read()
    names = TOMLFile(layout.names_config_path).read()

    assert load_order["loose-files"]["load-order"] == ["Pretty Armor", "Pretty Weapon"]

    armor_hash_id = names["loose-files"]["Pretty Armor"]
    weapon_hash_id = names["loose-files"]["Pretty Weapon"]
    assert armor_hash_id != weapon_hash_id
    assert (layout.mods_path / armor_hash_id / "Textures" / "armor.dds").exists()
    assert (layout.mods_path / weapon_hash_id / "Textures" / "weapon.dds").exists()
