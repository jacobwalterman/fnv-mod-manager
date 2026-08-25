import os
import subprocess

import fnv_mod_manager.fs as fs

WINE_PREFIX = fs.PREFIX_PATH
PROTONPATH = "GE-Proton"
GAMEID = "0"

REGISTRY_NAME = (
    "HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\Bethesda Softworks\\FalloutNV"
)
STRING_KEY_NAME = "Installed Path"

path_to_game = fs.SYMLINKED_GAME_PATH

# TODO: this currently assumes the gamefiles are outside of the prefix
stripped_root_and_separators = [piece for piece in path_to_game.parts[1::]]
joined = "\\".join(stripped_root_and_separators)
REGISTRY_STRING_KEY_VALUE = f"Z:\\{joined}\\"


def run_umu(args, **kwargs):
    env = os.environ.copy()
    env["WINEPREFIX"] = str(WINE_PREFIX)
    env["PROTONPATH"] = PROTONPATH
    env["GAMEID"] = GAMEID
    kwargs.setdefault("env", env)
    kwargs.setdefault("check", True)
    return subprocess.run(["umu-run", *args], **kwargs)


def create_prefix():
    # winetricks always boots the prefix before doing anything else, and
    # list-installed installs nothing, so this is just "create an empty prefix"
    run_umu(["winetricks", "list-installed"])


def write_registry_key():
    run_umu(
        [
            "reg",
            "add",
            REGISTRY_NAME,
            "/v",
            STRING_KEY_NAME,
            "/t",
            "REG_SZ",
            "/d",
            REGISTRY_STRING_KEY_VALUE,
            "/f",
        ]
    )


def launch_game():
    run_umu([str(path_to_game / "FalloutNV.exe")], cwd=str(path_to_game))


if __name__ == "__main__":
    create_prefix()
    write_registry_key()
    # insert FalloutCustom.ini into prefix
    fs.SYMLINKED_FALLOUT_CUSTOM_INI_PATH.symlink_to(fs.FALLOUT_CUSTOM_INI_PATH)
    # launch_game()
