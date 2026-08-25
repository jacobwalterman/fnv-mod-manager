from functools import cache
from pathlib import Path

import tomllib

from fnv_mod_manager.fs import Layout

LOOSE_FILES_KEY = "loose-files"
ESP_FILES_KEY = "esps"
LOAD_ORDER_KEY = "load-order"


@cache
def _load_toml(configuration_file) -> dict:
    with open(configuration_file, "rb") as f:
        return tomllib.load(f)


def load_sugared_names_mapping(configuration_file, file_type_key) -> dict:
    return _load_toml(configuration_file)[file_type_key]


# returns the desugared name if sugared otherwise returns the name
def desugar_file(name: str, configuration_file, file_type_key: str) -> str:
    return load_sugared_names_mapping(configuration_file, file_type_key).get(name, name)


def desugar_files(sugared_files, configuration_file, file_type_key):
    return [
        desugar_file(file, configuration_file, file_type_key) for file in sugared_files
    ]


# TODO: use this and make a default folder
def make_default_load_order_configuration_file(configuration_file: Path):
    with open(configuration_file, "w") as f:
        f.write(
            f"[{LOOSE_FILES_KEY}]\n{LOAD_ORDER_KEY} = \
            []\n\n[{ESP_FILES_KEY}]\n{LOAD_ORDER_KEY} = []"
        )


# TODO: use this and make a default folder
def make_default_sugared_names_configuration_file(configuration_file: Path):
    with open(configuration_file, "w") as f:
        f.write(f"[{LOOSE_FILES_KEY}]\n[{ESP_FILES_KEY}]\n")


def access_load_order_from_configuration(
    configuration_file, file_type_key: str
) -> list[str]:
    return _load_toml(configuration_file)[file_type_key][LOAD_ORDER_KEY]


def get_desugared_load_order(
    load_order_configuration: Path,
    sugared_names_configuration: Path,
    file_type_key: str,
):
    raw_load_order = access_load_order_from_configuration(
        load_order_configuration, file_type_key
    )
    desugared_load_order = desugar_files(
        raw_load_order, sugared_names_configuration, file_type_key
    )
    return desugared_load_order


def read_configuration_file_for_load_orders(layout: Layout):
    loose_files = get_desugared_load_order(
        layout.load_order_configuration_path, layout.names_config_path, LOOSE_FILES_KEY
    )
    esps = get_desugared_load_order(
        layout.load_order_configuration_path, layout.names_config_path, ESP_FILES_KEY
    )
    absolute_loose_files = [layout.loose_files_path / path for path in loose_files]
    absolute_esps = [layout.esps_path / path for path in esps]
    return absolute_loose_files, absolute_esps


def get_load_orders(layout: Layout):
    return read_configuration_file_for_load_orders(layout)
