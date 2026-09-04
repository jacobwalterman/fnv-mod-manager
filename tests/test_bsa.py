import os

import pytest

from fnv_mod_manager.bsa import build_dummy_bsa, tesHash

REAL_BSA_PATH = os.path.join(os.path.dirname(__file__), "Fallout - Invalidation.bsa")


def test_tes_hash_empty_string_does_not_crash():
    assert tesHash("") == 0


def test_tes_hash_dummy_dds_matches_known_value():
    # Verified against MO2's compiled genHash() and against the real
    # invalidation BSA below.
    assert tesHash("dummy.dds") == 0x8E50C6FD6405EDF9


def test_build_dummy_bsa_matches_real_invalidation_bsa_byte_for_byte():
    """
    The strongest test available: compares our generated output against
    an actual "Fallout - Invalidation.bsa" pulled from a working FNV mod
    manager setup. If this passes, our generator produces a file that's
    known to work for real archive invalidation, not just structurally
    plausible.
    """
    if not os.path.exists(REAL_BSA_PATH):
        pytest.skip(f"reference file not found at {REAL_BSA_PATH}")

    with open(REAL_BSA_PATH, "rb") as f:
        expected = f.read()

    actual = build_dummy_bsa("dummy.dds")

    assert actual == expected, (
        "Generated BSA differs from the known-working reference file. "
        "Check header fields, hash computation, and offset arithmetic."
    )
