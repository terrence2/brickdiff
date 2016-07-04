from .brick import *
from collections import defaultdict
import logging

log = logging.getLogger("database")


class Database:
    def __init__(self):
        self.sets = defaultdict(list)
        self.orders = defaultdict(list)
        self.bricks = {}

    def add_set(self, set: LegoSet):
        if set.no in self.sets:
            log.warning("Set {} is already present, adding duplicate bricks!".format(set.no))

        # Add to the set lists.
        self.sets[set.no].append(set)

        # Add the bricks to the brick piles.
        for brick_provision in set.brick_provisions:
            if brick_provision.brick.no not in self.bricks:
                self.bricks[brick_provision.brick.no] = BrickPile(brick_provision.brick)
            self.bricks[brick_provision.brick.no].add(brick_provision.number_provided())

    def remove_set(self, set: LegoSet):
        if set.no not in self.sets:
            log.warning("The set {} is not present in the collection!".format(set.no))
            return
        self.sets[set.no].pop()

        for brick_provision in set.brick_provisions:
            self.bricks[brick_provision.brick.no].remove(brick_provision.number_provided())

    def diff(self, target_bom: BrickManifest) -> BrickManifest:
        manifest = BrickManifest()
        for pile in target_bom.piles.values():
            if pile.brick.no not in self.bricks:
                manifest.add_required_bricks(pile.brick, pile.quantity)
            else:
                available = self.bricks[pile.brick.no].quantity
                if available < pile.quantity:
                    manifest.add_required_bricks(pile.brick, pile.quantity - available)
        return manifest