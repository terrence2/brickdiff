from collections import namedtuple
from typing import Union, Optional, List
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

    def __str__(self) -> str:
        return "${0.min:.4f} - ${0.avg:.4f} - ${0.max:.4f} | {0.quantity} in {0.stores_stocking} stores".format(self)


class Prices:
    """
    Describes both new and used prices for an item.
    """
    def __init__(self, new_prices: PriceGuide, used_prices: PriceGuide):
        self.new_prices = new_prices
        self.used_prices = used_prices

    def info(self) -> str:
        return "New:  {0.new_prices}\nUsed: {0.used_prices}".format(self)


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
  Brick Count:   {2}
  Dimensions:    {0.dimensions}
  Year Released: {0.year_released}
  Category ID:   {0.category_id}
  New:           {1.new_prices}
  Used:          {1.used_prices}""".format(self, prices, sum((p.number_provided() for p in self.brick_provisions)))
LegoSet = memoize(_LegoSet)

'''
class Brick:
    def __init__(self, partno: str, element_id: str, color: Color, name: str):
        # A unique identification (local) of this part. We'd use element_id, but those
        # are not entirely unique, depending on lego's current binning process, apparently.
        # In theory BL's color binning should be better at deduping.
        self.uid = partno + '-' + str(color.bricklink_id)

        # LEGO's identifier for this class of part.
        self.partno = partno

        # LEGO's element identifier. May be somewhat incorrect depending on the vagaraties of how
        # a set was parted out and when.
        self.element_id = element_id

        # The specific color of the part.
        self.color = color

        # The long, color independent name of the part.
        self.name = name

        # Any additional element ids.
        self.alternate_element_ids = []

    def add_alternate_element_id(self, element_id: str):
        assert element_id not in self.alternate_element_ids
        self.alternate_element_ids.append(element_id)

    def __lt__(self, other):
        return self.partno < other.partno

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        equal = self.uid == other.uid
        if equal:
            assert self.color == other.color
            #assert self.name == other.name, "{} == {}".format(self.name, other.name)
            #assert self.image_url == other.image_url, "{} == {}".format(self.image_url, other.image_url)
        return equal

    def is_usable_as(self, other) -> bool:
        """Ignores color -- used for mode = 'any'."""
        return other.partno == self.partno or other.name == self.name

    def is_similar_to(self, other) -> bool:
        """
        Some parts have been redesigned and have a new number, but the same name. These are generally
        inter-changeable.
        """
        # FIXME: this needs to understand what parts can be safely colorswapped at no cost... Bearings generally.
        if other.partno == '32123':
            assert other.name == '1/2Bush'
            return self.partno == '32123'
        if other.partno == '32054':
            assert other.name == '2MFric.SnapW/CrossHole'
            return self.partno == '32054'
        same_with_color = (
            (other.partno == self.partno and other.color == self.color) or  # This should be covered by __eq__
            (other.name == self.name and other.color == self.color)
        )
        return same_with_color

    def __str__(self):
        return "{:>8}: {} ({})".format(self.partno, self.name, self.color)

    def dump(self):
        print(str(self))
'''

