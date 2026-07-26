from fnv_mod_manager import merge_mods

def test_single_mod_creates_expected_symlinks(tmp_path):
    mod_a = tmp_path / "mod_a"
    (mod_a / "Textures").mkdir(parents=True)
    (mod_a / "Textures" / "armor.dds").write_text("fake texture data")

    target = tmp_path / "merged"
    merge_mods([mod_a], target)

    linked_file = target / "Textures" / "armor.dds"
    assert linked_file.is_symlink()
    assert linked_file.resolve() == (mod_a / "Textures" / "armor.dds").resolve()

def test_first_mod_wins_on_conflict(tmp_path):
    mod_a = tmp_path / "mod_a"
    mod_b = tmp_path / "mod_b"
    mod_a.mkdir()
    mod_b.mkdir()
    (mod_a / "armor.dds").write_text("mod a version")
    (mod_b / "armor.dds").write_text("mod b version")

    target = tmp_path / "merged"
    merge_mods([mod_a, mod_b], target)

    linked_file = target / "armor.dds"
    assert linked_file.resolve() == (mod_a / "armor.dds").resolve()
