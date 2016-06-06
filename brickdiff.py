#!/usr/bin/env python3
import argparse
import contextlib
import logging
import os.path
import shelve
import shutil
from brickdiff.lib.database import Database
from brickdiff.sources.wrapper import BrickLink
from collections import defaultdict
from pprint import pprint


log = logging.getLogger("brickdiff")


@contextlib.contextmanager
def global_state():
    path = os.path.realpath('.lego')
    bl = BrickLink(os.path.join(".lego", "cache"), os.path.join(".lego", "credentials", "bricklink.json"))
    with shelve.open(os.path.join(path, "database.shelve")) as db:
        try:
            copy = db['db']
            yield (bl, copy)
            db['db'] = copy
        finally:
            pass

def handle_init(args):
    path = os.path.realpath('.lego')
    print("Initializing LEGO database in {}".format(path))
    os.makedirs(path, 0o755, True)
    os.makedirs(os.path.join(path, "credentials"), 0o755, True)
    shutil.copyfile(args.bricklink_credentials[0], os.path.join(path, "credentials", "bricklink.json"))
    os.makedirs(os.path.join(path, "cache"), 0o755, True)
    os.makedirs(os.path.join(path, "cache", "color"), 0o755, True)
    os.makedirs(os.path.join(path, "cache", "element_id"), 0o755, True)
    os.makedirs(os.path.join(path, "cache", "parts"), 0o755, True)
    os.makedirs(os.path.join(path, "cache", "set_info"), 0o755, True)
    os.makedirs(os.path.join(path, "cache", "set_items"), 0o755, True)
    os.makedirs(os.path.join(path, "cache", "known_colors"), 0o755, True)
    os.makedirs(os.path.join(path, "cache", "prices_new"), 0o755, True)
    os.makedirs(os.path.join(path, "cache", "prices_used"), 0o755, True)
    with shelve.open(os.path.join(path, "database.shelve")) as db:
        db['db'] = Database()


def handle_add(args):
    with global_state() as (bl, db):
        for set_name in args.set:
            db.add_set(bl.get_set(set_name))


def handle_remove(args):
    with global_state() as (bl, db):
        for set_name in args.set:
            db.remove_set(bl.get_set(set_name))


def handle_info(args):
    with global_state() as (bl, db):
        for set_name in args.set:
            set = bl.get_set(set_name)
            prices = bl.get_set_prices(set)
            print(set.info(prices))

        for part_no in args.part:
            part = bl.get_part(part_no)
            colors = bl.get_all_part_colors(part)
            print(part.info(colors))

        for color_name in args.color:
            print(bl.get_color(color_name).info())

        for brick_name in args.brick:
            part_no, _, color_id = brick_name.partition(":")
            brick = bl.get_brick(part_no, color_id)
            prices = bl.get_brick_prices(brick)
            print(brick.info(prices))


def handle_list(args):
    with global_state() as (bl, db):
        if args.sets:
            for lego_set_list in db.sets.values():
                for lego_set in lego_set_list:
                    print(lego_set)

        if args.bricks:
            sort_key = lambda p: p.brick.part.name
            for brick_pile in sorted(db.bricks.values(), key=sort_key):
                print(brick_pile)


def handle_price(args):
    with global_state() as (bl, db):
        for name in args.brick:
            part_no, _, color_id = name.partition(":")
            log.info("Looking up prices for brick {}:{}".format(part_no, color_id))
            brick = bl.get_brick(part_no, int(color_id))
            prices = bl.get_brick_prices(brick)
            print(prices.info())

        for no in args.set:
            lego_set = bl.get_set(no)
            prices = bl.get_set_prices(lego_set)
            print(prices.info())

        for no in args.set_bricks:
            totals_new = [0, 0, 0]
            totals_used = [0, 0, 0]
            lego_set = bl.get_set(no)
            pairs = []
            for provision in lego_set.brick_provisions:
                prices = bl.get_brick_prices(provision.brick)
                totals_new[0] += provision.number_required() * prices.new_prices.min
                totals_new[1] += provision.number_required() * prices.new_prices.avg
                totals_new[2] += provision.number_required() * prices.new_prices.max
                totals_used[0] += provision.number_required() * prices.used_prices.min
                totals_used[1] += provision.number_required() * prices.used_prices.avg
                totals_used[2] += provision.number_required() * prices.used_prices.max
                pairs.append((provision, prices))
            for provision, prices in pairs:
                print("{} x {}: {}".format(provision.number_required(), provision.brick.no, provision.brick.part.name))
                print("  New:  {}".format(prices.new_prices))
                print("  Used: {}".format(prices.used_prices))
            print("Cost of all bricks in set (new):")
            print("  Min: ${:.2f}".format(totals_new[0]))
            print("  Avg: ${:.2f}".format(totals_new[1]))
            print("  Max: ${:.2f}".format(totals_new[2]))
            print("Cost of all bricks in set (used):")
            print("  Min: ${:.2f}".format(totals_used[0]))
            print("  Avg: ${:.2f}".format(totals_used[1]))
            print("  Max: ${:.2f}".format(totals_used[2]))

        for no in args.part:
            part = bl.get_part(no)
            colors = bl.get_all_part_colors(part)
            for color in colors:
                brick = bl.get_brick(part.no, color.no)
                prices = bl.get_brick_prices(brick)
                print("{} - {}: {} | {}".format(color.id, color.name, prices.new_prices, prices.used_prices))


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

    remove_parser = subparsers.add_parser('remove', help="Remove sets or components to the database.")
    remove_parser.add_argument("--set", "-s", nargs="*", type=str, help="A set id")
    remove_parser.set_defaults(func=handle_remove)

    list_parser = subparsers.add_parser('list', help="List contents of the database.")
    list_parser.add_argument("--sets", "-s", action="store_true", help="Show all sets.")
    list_parser.add_argument("--bricks", "-b", action="store_true", help="Show all bricks.")
    list_parser.set_defaults(func=handle_list)

    info_parser = subparsers.add_parser('info', help="Get detailed info about a set, part, brick, or color.")
    info_parser.add_argument("--set", "-s", nargs="*", type=str, default=[], help="A set id")
    info_parser.add_argument("--part", "-p", nargs="*", type=str, default=[], help="A part number")
    info_parser.add_argument("--color", "-c", nargs="*", type=int, default=[], help="A color number")
    info_parser.add_argument("--brick", "-b", nargs="*", type=str, default=[], help="A brick id (part:color)")
    info_parser.set_defaults(func=handle_info)

    price_parser = subparsers.add_parser('price', help="Find prices for things.")
    price_parser.add_argument("--part", "-p", nargs="*", default=[], help="A brick of any color")
    price_parser.add_argument("--brick", "-b", nargs="*", default=[], help="A specific brick")
    price_parser.add_argument("--set", "-s", nargs="*", default=[], help="A specific set")
    price_parser.add_argument("--set-bricks", "-S", nargs="*", default=[], help="Cost of all bricks in a set.")
    price_parser.set_defaults(func=handle_price)

    args = main_parser.parse_args()
    args.func(args)
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
