#!/usr/bin/env python3
import argparse
import os.path
import logging
import shutil
from brickdiff.sources.wrapper import BrickLink


def handle_init(args):
    path = os.path.realpath('.lego')
    print("Initializing LEGO database in {}".format(path))
    os.makedirs(path, 0o755, False)
    os.makedirs(os.path.join(path, "credentials"), 0o755, False)
    shutil.copyfile(args.bricklink_credentials[0], os.path.join(path, "credentials", "bricklink.json"))
    os.makedirs(os.path.join(path, "cache"), 0o755, False)
    os.makedirs(os.path.join(path, "cache", "color"), 0o755, False)
    os.makedirs(os.path.join(path, "cache", "element_id"), 0o755, False)
    os.makedirs(os.path.join(path, "cache", "parts"), 0o755, False)
    os.makedirs(os.path.join(path, "cache", "set_info"), 0o755, False)
    os.makedirs(os.path.join(path, "cache", "set_items"), 0o755, False)
    os.makedirs(os.path.join(path, "sets"), 0o755, False)


def handle_add(args):
    bl = BrickLink(os.path.join(".lego", "cache"), os.path.join(".lego", "credentials", "bricklink.json"))
    for set_name in args.set:
        print("adding set {}".format(set_name))
        lego_set = bl.get_set(set_name)
        print(lego_set)


def handle_list(args):
    print("Handling add...")


def main():
    logging.basicConfig(level='DEBUG')

    main_parser = argparse.ArgumentParser(prog="brickdiff", description="Mange a LEGO database.")
    subparsers = main_parser.add_subparsers(help="sub-command help")

    init_parser = subparsers.add_parser('init', help="Initialize a new LEGO repository.")
    init_parser.add_argument("bricklink_credentials", nargs=1)
    init_parser.set_defaults(func=handle_init)

    add_parser = subparsers.add_parser('add', help="Add sets or components to the database.")
    add_parser.add_argument("--set", "-s", nargs="*", type=str, help="A set id")
    add_parser.set_defaults(func=handle_add)

    list_parser = subparsers.add_parser('list', help="List contents of the database.")
    list_parser.add_argument("--all", "-a", action="store_true", help="Show all contents")
    list_parser.set_defaults(func=handle_list)

    args = main_parser.parse_args()
    args.func(args)
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
