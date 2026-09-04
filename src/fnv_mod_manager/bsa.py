import os
import struct


def flags_to_int(flag_bits: dict[str, int], flags: set[str]) -> int:
    value = 0
    for name in flags:
        value |= flag_bits[name]
    return value


def create_archive_flags_integer():
    ARCHIVE_FLAG_BITS = {
        "include_dir_names": 0x1,
        "include_file_names": 0x2,
        "compressed": 0x4,
        "retain_directory_names": 0x8,
        "retain_file_names": 0x10,
        "retain_file_name_offsets": 0x20,
        "xbox_360_archive": 0x40,
        "retain_strings_during_startup": 0x80,
        "embed_file_names": 0x100,
        "xmem_codec": 0x200,
    }
    always_set_bits = {"include_dir_names", "include_file_names"}
    return flags_to_int(ARCHIVE_FLAG_BITS, always_set_bits)


def create_file_flags_integer():
    FILE_FLAG_BITS = {
        "meshes": 0x1,
        "textures": 0x2,
        "menus": 0x4,
        "sounds": 0x8,
        "voices": 0x10,
        "shaders": 0x20,
        "trees": 0x40,
        "fonts": 0x80,
        "miscellaneous": 0x100,
    }
    set_bits = {"textures"}
    return flags_to_int(FILE_FLAG_BITS, set_bits)


# courtesy of UESP
def tesHash(file_name):
    root, ext = os.path.splitext(file_name.lower())
    root = root.replace("/", "\\")

    chars = list(map(ord, root))
    if not chars:
        return 0  # empty root (e.g. the "" folder name) - nothing to hash

    second_last = chars[-2] if len(chars) > 2 else 0
    hash1 = chars[-1] | second_last << 8 | len(chars) << 16 | chars[0] << 24
    if ext == ".kf":
        hash1 |= 0x80
    elif ext == ".nif":
        hash1 |= 0x8000
    elif ext == ".dds":
        hash1 |= 0x8080
    elif ext == ".wav":
        hash1 |= 0x80000000

    uintMask, hash2, hash3 = 0xFFFFFFFF, 0, 0
    for char in chars[1:-2]:
        hash2 = ((hash2 * 0x1003F) + char) & uintMask
    for char in map(ord, ext):
        hash3 = ((hash3 * 0x1003F) + char) & uintMask
    hash2 = (hash2 + hash3) & uintMask

    return (hash2 << 32) + hash1


HEADER_LENGTH = 36
FOLDER_RECORD_SIZE = 16  # v104: 8-byte hash + 4-byte count + 4-byte offset
FILE_RECORD_SIZE = 16  # 8-byte hash + 4-byte size + 4-byte offset


def build_dummy_bsa(file_name: str = "dummy.dds") -> bytes:
    file_ID = b"BSA\x00"
    version = 104
    archive_flags = create_archive_flags_integer()
    folder_count = 1
    file_count = 1

    folder_name = b"\x00"  # hardcoded "" folder name, zero terminated
    total_folder_name_length = len(folder_name)

    file_name_bytes = file_name.encode("ascii") + b"\x00"
    total_file_name_length = len(file_name_bytes)

    file_flags = create_file_flags_integer()
    padding = 0

    header = struct.pack(
        "<4sIIIIIIIHH",
        file_ID,
        version,
        HEADER_LENGTH,
        archive_flags,
        folder_count,
        file_count,
        total_folder_name_length,
        total_file_name_length,
        file_flags,
        padding,
    )

    folder_name_hash = tesHash("")
    # per the wiki spec: this field = actual offset of [folder name + file record]
    # plus totalFileNameLength
    folder_offset_field = HEADER_LENGTH + FOLDER_RECORD_SIZE + total_file_name_length
    folder_record = struct.pack(
        "<QII", folder_name_hash, file_count, folder_offset_field
    )

    file_hash = tesHash(file_name)
    file_size = 0  # dummy file, no real data

    # Matches MO2's own DummyBSA constant (0x44 + filename_len + 4). For this
    # single 0-byte file it lands on the file's last byte; harmless since size=0
    # means nothing ever gets read from it. Kept as-is to match the verified real file.
    file_offset_field = 0x44 + total_file_name_length + 4
    file_record = struct.pack("<QII", file_hash, file_size, file_offset_field)

    trailing_zero_pad = b"\x00\x00\x00\x00"

    return (
        header
        + folder_record
        + folder_name
        + file_record
        + file_name_bytes
        + trailing_zero_pad
    )


def write_dummy_bsa(path: str, file_name: str = "dummy.dds") -> None:
    with open(path, "wb") as f:
        f.write(build_dummy_bsa(file_name))


if __name__ == "__main__":
    write_dummy_bsa("dummy_output.bsa")
