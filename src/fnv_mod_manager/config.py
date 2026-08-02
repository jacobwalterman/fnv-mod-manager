from functools import cache
from pathlib import Path

import tomllib
import fnv_mod_manager.fs as fs

@cache
def _load_sugared_names_mapping() -> dict:
    with open(fs.NAMES_CONFIG_PATH, "rb") as f:
        return tomllib.load(f)

# returns the sugared name if sugared otherwise returns the name
def desugar_name(name: str) -> str:
    return _load_sugared_names_mapping().get(name, name)

# TODO: use this and make a default folder
def make_default_configuration_file():
    with open(fs.LOAD_ORDER_CONFIGURATION_PATH, "w") as f:
        f.write('[loose-files]\nload-order = []\n\n[esps]\nload-order = []')

def read_configuration_file_for_load_orders(configuration_file):
    with open(configuration_file, "rb") as f:
        loose_and_esp_dicts = tomllib.load(f)
        loose_files, esps = loose_and_esp_dicts["loose-files"]["load-order"], loose_and_esp_dicts["esps"]["load-order"]
    for pretty_file in [loose_files, esps]:
        for i, file in enumerate(pretty_file):
            pretty_file[i] = desugar_name(file)
    absolute_loose_files = [fs.LOOSE_FILES_PATH / path for path in loose_files]
    absolute_esps = [fs.ESPS_PATH / path for path in esps]
    return absolute_loose_files, absolute_esps 

def get_load_orders():
    return read_configuration_file_for_load_orders(fs.LOAD_ORDER_CONFIGURATION_PATH)
