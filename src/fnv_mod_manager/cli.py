import argparse

CLI_NAME = 'fnvmm'

def install(args):
    filepath = args.filepath



parser = argparse.ArgumentParser(
                    prog=f'{CLI_NAME}',
                    description='Manages fnv mod manager',
                    epilog='I care about user issues, so please make a polite report/question if you have any persistent/unresolved issues! I consider things like confusion and "stupid mistakes"\
                            to be ux issues and I\'m interested in addressing them, so don\'t be shy :).',
                    )

parser.add_argument('filename')

subparsers = parser.add_subparsers(
                            title='subcommands',
                            description='valid subcommands',
                            )

parser_install = subparsers.add_parser('install', help='this verb is used to install files into your mods folder for management by ')
parser_install.add_argument('filename', type=str, help='this argument should be the path of the file you want to install into your mods folder.')
parser_install.set_defaults(func=install)

args = parser.parse_args()
if __name__ == "__main__":
    x = 1
