import csv
from collections import namedtuple
from typing import Union, Optional, List
from enum import Enum
from pprint import pprint


Image = namedtuple("Image", ['url', 'thumbnail_url'])


def indent(lines: str, spaces: int = 2):
    out = []
    for line in lines.split('\n'):
        out.append(' ' * spaces + line)
    return '\n'.join(out)


class Dimensions:
    def __init__(self, x: str, y: str, z: str, weight: str):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.weight = float(weight)

    def __str__(self) -> str:
        return "({0.x}s, {0.y}s, {0.z}s) @ {0.weight}g".format(self)


_memoized = {}
def memoize(wrapped_cls):
    class Wrapper(wrapped_cls):
        def __new__(cls, ident: Union[str, int], name: str, *args, **kwargs):
            key = str(ident) + ":" + name
            if key in _memoized:
                return _memoized[key]
            instance = wrapped_cls(ident, name, *args, **kwargs)
            instance.__dict__['wrapped_cls'] = wrapped_cls
            return instance
        __doc__ = property(lambda self:self.wrapped_cls.__doc__)
        __module__ = property(lambda self:self.wrapped_cls.__module__)

        def __name__(self):
            print("Wrapped name is: {}".format(self.wrapped_cls.__name__))
            return self.wrapped_cls.__name__
        #__name__ = property(lambda self:self.wrapped_cls.__name__)
    return Wrapper


class _Color:
    """
    A color. I think the code is like dye lot, maybe?
    """
    def __init__(self, ident: int, name: str, code: str, type: str):
        self.id = ident
        self.name = name
        self.code = code
        self.type = type

    def __str__(self) -> str:
        return "{0.id} - {0.name}".format(self)

    def info(self) -> str:
        return """Color {0.id}: {0.name}
  Code: {0.code}
  Type: {0.type}""".format(self)

    @staticmethod
    def none():
        return Color(0, "NotAColor", "0", "notacolor")
Color = memoize(_Color)


class _Part:
    """
    The concept of a lego brick without color and encompassing multiple design revisions.
    Many Bricks may share a Shape: all are physically compatible (although the colors may
    be sickening).
    """
    def __init__(self, no: str, name: str, category_id: int, dimensions: Dimensions, image: Image,
                 is_obsolete: bool, year_released: int):
        self.no = no
        self.name = name
        self.category_id = category_id
        self.dimensions = dimensions
        self.image = image
        self.is_obsolete = is_obsolete
        self.year_released = year_released

    def info(self, colors: Optional[List[Color]] = None) -> str:
        base = """Part {0.no} - {0.name}
  Year Released: {0.year_released}
  Dimensions:    {0.dimensions}
  Is Obsolete:   {0.is_obsolete}
  Category ID:   {0.category_id}""".format(self)
        if not colors:
            return base
        color_str = """
  Colors:\n{}""".format(indent('\n'.join((str(c) for c in colors)), 4))
        return base + color_str
Part = memoize(_Part)


class Brick:
    """
    A LEGO part with a specific color.
    """
    def __init__(self, part: Part, color: Color, element_ids: [str]):
        # Generate a UID for this part/color combo.
        self.no = part.no + ":" + str(color.id)

        # The part and color.
        self.part = part
        self.color = color

        # A list of compatible LEGO elements.
        self.element_ids = element_ids

    def __str__(self):
        return "{:>11}:{:03}".format(self.part.no, self.color.id)

    def info(self, prices):
        return """Brick {0.part.no}:{0.color.id}
{1}
{2}
  Prices:
{3}""".format(self, indent(self.part.info()), indent(self.color.info()), indent(prices.info(), 4))


class PriceGuide:
    """
    Price statistics for an item.
    """
    def __init__(self, prices: dict):
        assert prices['currency_code'] == 'USD'
        self.is_new_or_used = prices['new_or_used'] == 'N'
        self.min = float(prices['min_price'])
        self.avg = float(prices['avg_price'])
        self.max = float(prices['max_price'])
        self.quantity = int(prices['total_quantity'])
        self.stores_stocking = int(prices['unit_quantity'])

    def show_short(self) -> str:
        return "${0.min:.4f} - ${0.avg:.4f} - ${0.max:.4f}".format(self)

    def __str__(self) -> str:
        return "${0.min:.4f} - ${0.avg:.4f} - ${0.max:.4f} | {0.quantity} in {0.stores_stocking} stores".format(self)


class PriceKind(Enum):
    new = 0
    used = 1


class Prices:
    """
    Describes both new and used prices for an item.
    """
    def __init__(self, new_prices: PriceGuide, used_prices: PriceGuide):
        self.prices_ = {
            PriceKind.new: new_prices,
            PriceKind.used: used_prices
        }

    def get(self, kind: PriceKind) -> PriceGuide:
        return self.prices_[kind]

    def info(self) -> str:
        return "New:  {}\nUsed: {}".format(self.prices_[PriceKind.new], self.prices_[PriceKind.used])

    """
    def __str__(self) -> str:
        return "New: {}; Used: {}".format(self.new_prices.show_short(), self.used_prices.show_short())
    """


class BrickPile:
    """
    A collection of lego bricks of a certain type.
    """
    def __init__(self, brick: Brick, quantity: int = 0):
        self.brick = brick
        self.quantity = quantity

    def add(self, n: int):
        self.quantity += n

    def remove(self, n: int):
        self.quantity = max(0, self.quantity - n)

    def __str__(self) -> str:
        return "{:5} - {}: {}".format(self.quantity, str(self.brick), self.brick.part.name[:70])


class PricedBrickPile(BrickPile):
    def __init__(self, pile: BrickPile, prices: Prices):
        super().__init__(pile.brick, pile.quantity)
        self.prices = prices

    def average_cost(self, kind: PriceKind):
        return self.prices.get(kind).avg * self.quantity

    def show(self, kind: PriceKind) -> str:
        return "{0.quantity:5} - {0.brick} - ${1:6.2f} - {2}".format(self, self.average_cost(kind),
                                                                     self.brick.part.name[:50])


class PriceAccumulator:
    """This convenience class handles adding all the internal prices in one location."""

    class PriceGuideAccumulator:
        def __init__(self):
            self.min = 0
            self.avg = 0
            self.max = 0

        def add(self, other: PriceGuide, count: int = 1):
            self.min += other.min * count
            self.avg += other.avg * count
            self.max += other.max * count
            return self

        def __str__(self) -> str:
            return "Min ${0.min:.2f} | Avg ${0.avg:.2f} | Max ${0.max:.2f}".format(self)

    def __init__(self):
        self.acc_ = {
            PriceKind.new: self.PriceGuideAccumulator(),
            PriceKind.used: self.PriceGuideAccumulator()
        }

    def add(self, other: Prices, count: int = 1):
        self.acc_[PriceKind.new].add(other.get(PriceKind.new), count)
        self.acc_[PriceKind.used].add(other.get(PriceKind.used), count)
        return self

    def info(self, kind: PriceKind) -> str:
        return str(self.acc_[kind])


class LegoSetBrickProvision:
    """
    These are the bricks of a type that a set provides.
    """
    def __init__(self, quantity: int, num_that_are_extra: int, brick: Brick):
        # The type of brick provided.
        self.brick = brick

        # The quantity of bricks that were provided. Note that this includes any
        # extra bricks that come with the set that are intended as spares.
        self.quantity = quantity

        # The number of spares of this type that were provided. Note that this class
        # describes the bricks a set provides. To find the number of bricks that are
        # required, this number must be subtracted from the quantity.
        self.num_that_are_extra = num_that_are_extra

    def number_provided(self):
        return self.quantity

    def number_required(self):
        return self.quantity - self.num_that_are_extra

    def __str__(self) -> str:
        return "{0.quantity:4} - {0.brick} {0.brick.part.name}".format(self)


class _LegoSet:
    def __init__(self, no: str, name: str, category_id: int, dimensions: Dimensions, image: Image,
                 is_obsolete: bool, year_released: int):
        super().__init__()
        self.no = no
        self.name = name
        self.category_id = category_id
        self.dimensions = dimensions
        self.image = image
        self.is_obsolete = is_obsolete
        self.year_released = year_released
        self.brick_provisions = []

    def add_brick_provision(self, brick_provision: LegoSetBrickProvision):
        self.brick_provisions.append(brick_provision)

    def __str__(self) -> str:
        return "{0.no:8} {0.name}".format(self)

    def info(self, prices: Prices) -> str:
        return """Set {0.no}: {0.name}
  Brick Count:   {count}
  Dimensions:    {0.dimensions}
  Year Released: {0.year_released}
  Category ID:   {0.category_id}
  New:           {new_prices}
  Used:          {old_prices}""".format(self,
                                        new_prices=prices.get(PriceKind.new),
                                        old_prices=prices.get(PriceKind.used),
                                        count=sum((p.number_provided() for p in self.brick_provisions)))
LegoSet = memoize(_LegoSet)


class BrickManifest:
    """
    A collection of brick piles representing brick requirements for something.
    """
    def __init__(self):
        self.piles = {}

    def add_required_bricks(self, brick: Brick, count: int):
        assert brick.no not in self.piles
        self.piles[brick.no] = BrickPile(brick, count)

    def note_brick_cost(self, brick: Brick, prices: Prices):
        """Convert a BrickPile into a PricedBrickPile."""
        assert brick.no in self.piles
        assert not isinstance(self.piles[brick.no], PricedBrickPile)
        self.piles[brick.no] = PricedBrickPile(self.piles[brick.no], prices)

    def pile_count(self):
        return len(self.piles)

    def brick_count(self):
        acc = 0
        for pile in self.piles.values():
            acc += pile.quantity
        return acc

    @classmethod
    def from_set(cls, lego_set: LegoSet) -> 'BrickManifest':
        out = cls()
        for provision in lego_set.brick_provisions:
            out.add_required_bricks(provision.brick, provision.number_required())
        return out

    def to_csv(self, filename: str):
        with open(filename, 'w+', newline='') as fp:
            w = csv.writer(fp)
            w.writerow("Part,Color,Num,Notes".split(","))
            for p in sorted(self.piles.values(), key=lambda k: k.brick.part.name):
                w.writerow([p.brick.part.no, p.brick.color.id, p.quantity,
                            p.brick.color.name + ' - ' + p.brick.part.name])

    @classmethod
    def from_csv(cls, filename: str, bl: 'BrickLink') -> 'BrickManifest':
        out = cls()
        with open(filename, 'r', newline='') as fp:
            r = csv.reader(fp)
            next(r)  # skip the header row
            for row in r:
                brick_no, color_id, quantity = row[:3]
                brick = bl.get_brick(brick_no, int(color_id))
                out.add_required_bricks(brick, int(quantity))
        return out



