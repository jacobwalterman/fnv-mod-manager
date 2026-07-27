import argparse
import subprocess
import sys

from fnv_mod_manager import fs

CLI_NAME = 'fnvmm'

def install(args):
    try:
        fs.extract_archive_to_mods_folder(args.filename)
    except subprocess.CalledProcessError:
        print(f"Error: failed to extract {args.filename}", file=sys.stderr)
        sys.exit(1)
    print(f"Installed {args.filename}")

def build_parser():
    parser = argparse.ArgumentParser(
        prog=CLI_NAME,
        description='Manages fnv mod manager',
        epilog='I care about user issues, so please make a polite report/question if you have any '
               'persistent/unresolved issues! I consider things like confusion and "stupid mistakes" '
               'to be ux issues and I\'m interested in addressing them, so don\'t be shy :).',
    )
    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands',
        required=True,
    )
    parser_install = subparsers.add_parser(
        'install',
        help='install a file into your mods folder for management',
    )
    parser_install.add_argument(
        'filename', type=str,
        help='the path of the file you want to install into your mods folder.',
    )
    parser_install.set_defaults(func=install)
    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
