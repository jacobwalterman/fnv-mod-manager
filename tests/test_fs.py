import pytest

import fnv_mod_manager.fs as fs


def test_remove_files_in_temp_clears_directory(tmp_path):
    (tmp_path / "leftover.txt").write_text("junk")
    (tmp_path / "leftover_dir").mkdir()

    fs.remove_files_in_temp(tmp_path)

    assert list(tmp_path.iterdir()) == []


def test_use_temp_dir_wipes_on_enter_and_exit(tmp_path):
    (tmp_path / "stale.txt").write_text("junk")

    with fs.use_temp_dir(tmp_path) as temp_dir:
        assert list(tmp_path.iterdir()) == []
        assert temp_dir == tmp_path
        (temp_dir / "scratch.txt").write_text("working")

    assert list(tmp_path.iterdir()) == []


def test_use_temp_dir_cleans_up_on_exception(tmp_path):
    with pytest.raises(ValueError):
        with fs.use_temp_dir(tmp_path) as temp_dir:
            (temp_dir / "scratch.txt").write_text("working")
            raise ValueError("boom")

    assert list(tmp_path.iterdir()) == []


def test_use_temp_hash_manifest_yields_given_path(tmp_path):
    manifest_path = tmp_path / "hash-manifest"

    with fs.use_temp_hash_manifest(manifest_path) as yielded_path:
        assert yielded_path == manifest_path
        assert not yielded_path.exists()
        yielded_path.write_text("some:manifest\n")

    assert not manifest_path.exists()


def test_use_temp_hash_manifest_removes_stale_file_on_enter(tmp_path):
    manifest_path = tmp_path / "hash-manifest"
    manifest_path.write_text("leftover")

    with fs.use_temp_hash_manifest(manifest_path) as yielded_path:
        assert not yielded_path.exists()


def test_use_temp_hash_manifest_cleans_up_on_exception(tmp_path):
    manifest_path = tmp_path / "hash-manifest"

    with pytest.raises(ValueError):
        with fs.use_temp_hash_manifest(manifest_path) as yielded_path:
            yielded_path.write_text("data")
            raise ValueError("boom")

    assert not manifest_path.exists()
