# fnvmm — Fallout: New Vegas Mod Manager

A Nix-inspired mod manager for Fallout: New Vegas. Mods are ingested into a content-addressable store and composed into a live game install as a symlink tree, so conflicts are resolved declaratively instead of by copying files around by hand.

Linux/Proton only as of now, as this project is intended to address the gap of Linux-native tooling, Linux is the primary focus. Windows support isn't planned, though a pull request adding it would be appreciated.

## Status

Core workflow (install, merge, load order, launch) is functional end to end. CLI and config-editing UX are still evolving; several design decisions noted below are intentionally provisional.

## What it does

- **Content-addressable store.** Mod archives are extracted, then hashed (the extracted content, not the raw archive bytes) to produce a stable file id. This dedupes storage when different mods bundle the same shared assets, and survives authors silently reuploading the "same" version with different bytes.
- **Symlink-tree merging.** The live game directory is never written to directly. Instead, an ordered list of mods is walked and merged into a "generation," a tree of symlinks pointing back into the store, which is what actually becomes the game's `Data` folder. Later entries in the load order win at any colliding path (index 0 = lowest priority, matching MO2's convention).
- **The base game is just a mod.** Vanilla FNV itself is treated as one entry at the root of the same merge process, rather than special-cased, so the whole install is produced by the same mechanism as any mod.
- **ESP/ESM and loose-file ordering.** Plugins and loose files are sorted and ordered separately for load-order purposes, including keeping master files loading before regular plugins.
- **`Data/`-root detection.** Mods that ship an explicit `Data/` folder at their archive root are detected and re-rooted so only the actual game content gets merged in, rather than being symlinked in as-is.
- **Pretty naming.** Install time prompts for a human-readable name per mod; the store key stays a hash, and the name is recorded separately so config files never reference ugly store paths directly.
- **Case normalization.** Paths are normalized for case (and separators) once at import time, since Bethesda's file references are case-insensitive but Linux paths aren't — this keeps store keys and conflict detection consistent.
- **Proton/launch setup.** Includes basic Proton prefix creation and symlinks `FalloutCustom.ini` into the prefix so ini overrides are managed the same declarative way as everything else.
- **Lazy default layout.** The default on-disk directory structure (store, generations, config) is created lazily on first use rather than requiring an explicit init step.

## Architecture

- `fs.py` — the content store: extraction, hashing, symlink tree construction, temp-dir handling during install.
- `Layout` — a frozen dataclass holding every real filesystem path the tool uses (store, mods dir, generations, live game dir, etc.), built via `build_layout()` / `default_layout()` and passed explicitly into functions that need it. Replaced earlier module-level path constants, since mutable globals didn't play well with monkeypatching in tests.
- `config.py` — reads and resolves the user's TOML configuration (installed mods, load order, ini overrides) against the store.
- `merge.py` — walks the ordered mod list and produces the symlinked generation.
- `cli.py` — the `fnvm` command-line entry point (e.g. `fnvm install <archive>`).

## Development

- Dependency/build tooling: `uv`, with `p7zip` used for archive extraction.
- Tests: `pytest`, covering `cli.py`, `merge.py`, and `fs.py`; a pre-push hook runs the suite.
- Linting/formatting: `ruff`. Type checking: `pyright`. Both wired into pre-commit.

## Known limitations / open design work

- Config-editing UX (real profiles, MO2-style separators, before/after ordering rules) is designed but not built; the current mechanism is a simpler explicit ordered list.
- No general conflict/rule engine yet — resolution today is priority-order last-wins, not the declarative "if A and B present, apply patch C" style rule system that's planned.
- ESP/ESM record-level merging (as opposed to whole-file loose merging) is explicitly out of scope for now.
- FOMOD-packaged installers aren't handled.
- Imperative "assembly" steps some mods need (BSA decompression, ESM fixes, the 4GB LAA patch, archive-invalidation ini flags) are still done by hand rather than automated by the tool.

## Roadmap

- Automate the imperative assembly steps above instead of doing them manually.
- CLI refinements, notably mod removal through the tool (currently manual).
- A possible curated baseline profile (NVSE, UIO, umu-launcher, and Viva New Vegas's recommended fixes) so a fresh setup works correctly out of the box, without redistributing third-party mod content in this repo.
