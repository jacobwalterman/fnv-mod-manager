import os
import subprocess

from fnv_mod_manager.fs import default_layout

layout = default_layout()
WINE_PREFIX = layout.prefix_path
PROTONPATH = "GE-Proton"
GAMEID = "0"

REGISTRY_NAME = (
    "HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\Bethesda Softworks\\FalloutNV"
)
STRING_KEY_NAME = "Installed Path"

path_to_game = layout.symlinked_game_path

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
    layout.symlinked_fallout_custom_ini_path.symlink_to(layout.fallout_custom_ini_path)
    # launch_game()
