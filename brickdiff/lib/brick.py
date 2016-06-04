from collections import namedtuple


Dimensions = namedtuple("Dimensions", 'x y z weight'.split())
Image = namedtuple("Image", 'url thumbnail_url'.split())


_memoized = {}
def memoize(wrapped_cls):
    class Wrapper(wrapped_cls):
        def __new__(cls, ident: str or int, name: str, *args, **kwargs):
            key = str(ident) + ":" + name
            if key in _memoized:
                return _memoized[key]
            return wrapped_cls(ident, name, *args, **kwargs)
    return Wrapper


@memoize
class Part:
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


@memoize
class Color:
    """
    A color. I think the code is like dye lot, maybe?
    """
    def __init__(self, ident: int, name: str, code: str, type: str):
        self.id = ident
        self.name = name
        self.code = code
        self.type = type

    @staticmethod
    def none():
        return Color(0, "NotAColor", "0", "notacolor")


class Brick:
    """
    A LEGO part with a specific color.
    """
    def __init__(self, part: Part, color: Color, element_ids: [str]):
        self.part = part
        self.color = color

        # A list of compatible LEGO elements.
        self.element_ids = element_ids


class BrickPile:
    """
    A pile of multiple bricks, as in part of a set. Contains
    information about set inclusion, like how many are extras.
    """
    def __init__(self, quantity: int, num_that_are_extra: int, brick: Brick):
        self.brick = brick
        self.quantity = quantity
        self.num_that_are_extra = num_that_are_extra


class BrickCollection:
    """
    A collection of brick piles. E.g. as describing a set. This is
    generally the base of something more meaningful like a set or order.
    """
    def __init__(self):
        self.brick_piles = []

    def add_brick_pile(self, brick_pile: BrickPile):
        self.brick_piles.append(brick_pile)


@memoize
class LegoSet(BrickCollection):
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

