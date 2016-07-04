from ..lib.brick import Color, Dimensions, Image, Part, Prices, PriceGuide, LegoSet, Brick, LegoSetBrickProvision
from .bricklink import api
from typing import List
from pprint import pformat, pprint
from datetime import datetime, timedelta
import os.path
import json
import html
import logging


log = logging.getLogger("bricklink")


class BrickLink:
    def __init__(self, cache_directory: str, credential_file: str):
        self.cache_directory = cache_directory
        with open("bricklink-token.json", "r") as fp:
            key_info = json.load(fp)
        self.client = api.ApiClient(consumer_key=key_info['consumer']['key'],
                                    consumer_secret=key_info['consumer']['secret'],
                                    access_token=key_info['access']['key'],
                                    access_token_secret=key_info['access']['secret'])

    def cached(self, subdir: str, timeout: timedelta, ident: str, fn: callable, *args):
        cache_file = os.path.join(self.cache_directory, subdir, ident)
        if os.path.exists(cache_file):
            last_modified = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if last_modified + timeout > datetime.now():
                with open(cache_file, "r") as fp:
                    data = json.load(fp)
                return data
        out = fn(*args)
        with open(cache_file, "w+") as fp:
            json.dump(out, fp)
        return out

    def get_part(self, no: str) -> Part:
        log.debug("fetching part number: {}".format(no))
        data = self.cached("parts", timedelta(weeks=52), no, self.client.catalog.getItem, "PART", no)
        assert data['no'] == no, pformat(data)
        assert data['type'] == 'PART', pformat(data)
        dim = Dimensions(data['dim_x'], data['dim_y'], data['dim_z'], data['weight'])
        img = Image(data['image_url'], data['thumbnail_url'])
        return Part(no, html.unescape(data['name']), data['category_id'], dim, img,
                    data['is_obsolete'], data['year_released'])

    def get_color(self, ident: int) -> Color:
        log.debug("fetching color id: {}".format(ident))
        data = self.cached("color", timedelta(weeks=52), str(ident), self.client.color.getColorDetail, ident)
        return Color(ident, data['color_name'], data['color_code'], data['color_type'])

    def get_brick(self, part_no: str, color_id: int) -> Brick:
        part = self.get_part(part_no)
        color = Color.none()
        if color_id != 0:
            color = self.get_color(color_id)

        # Query all LEGO element_ids that this part/color has been released as.
        element_ids = []
        elements = self.cached("element_id", timedelta(weeks=4), part.no + '-' + str(color.id),
                               self.client.item_mapping.getElementID, part.no, color.id)
        if not elements:
            elements = self.cached("element_id", timedelta(weeks=4), part.no,
                                   self.client.item_mapping.getElementID, part.no)
        for element in elements:
            element_ids.append(element['element_id'])

        return Brick(part, color, element_ids)

    def get_set(self, no: str):
        data = self.cached("set_info", timedelta(weeks=4), no, self.client.catalog.getItem, 'SET', no)
        assert data['type'] == 'SET'
        dim = Dimensions(data['dim_x'], data['dim_y'], data['dim_z'], data['weight'])
        img = Image(data['image_url'], data['thumbnail_url'])
        lego_set = LegoSet(no, data['name'], data['category_id'], dim, img, data['is_obsolete'], data['year_released'])
        item_data = self.cached("set_items", timedelta(weeks=4), no, self.client.catalog.getSubsets, 'SET', no)
        for entry in item_data:
            for item in entry['entries']:
                # FIXME: We only care about bricks for now.
                if item['item']['type'] != 'PART':
                    log.warning("Unrecognized item type in set: {}".format(item['item']['type']))
                    continue

                # Load the brick.
                brick = self.get_brick(item['item']['no'], item['color_id'])

                # TODO: what are is_alternate and is_counterpart?
                extras = item['extra_quantity']
                quantity = item['quantity'] + extras
                provision = LegoSetBrickProvision(quantity, extras, brick)
                lego_set.add_brick_provision(provision)

                """
                'color_id': 11,
                'extra_quantity': 0,
                'is_alternate': False,
                'is_counterpart': True,
                'item': {'category_id': 777,
                         'name': 'Technic, Liftarm 1 x 11 Thick with &#39;L350F&#39; and '
                                 'Yellow End Pattern Model Right Side &#40;Sticker&#41; - Set '
                                 '42030',
                         'no': '32525pb015R',
                         'type': 'PART'},
                'quantity': 1}
                """

        return lego_set

    def get_brick_supersets(self, brick: Brick) -> List[LegoSet]:
        data = self.cached("supersets", timedelta(weeks=4), brick.no,
                           self.client.catalog.getSupersets, "PART", brick.part.no, brick.color.id)
        all_sets = []
        for entry in data[0]['entries']:
            lego_set = self.get_set(entry['item']['no'])
            all_sets.append(lego_set)
        return all_sets

    def get_all_part_colors(self, part: Part) -> List[Color]:
        data = self.cached("known_colors", timedelta(weeks=1), part.no,
                           self.client.catalog.getKnownColors, 'PART', part.no)
        return [self.get_color(item['color_id']) for item in data]

    def get_brick_prices(self, brick: Brick) -> Prices:
        new_prices = self.cached("prices_new", timedelta(weeks=1), brick.no, self.client.catalog.getPriceGuide,
                                 'PART', brick.part.no, brick.color.id, None, 'N', 'Y')
        used_prices = self.cached("prices_used", timedelta(weeks=1), brick.no, self.client.catalog.getPriceGuide,
                                  'PART', brick.part.no, brick.color.id, None, 'U', 'Y')
        return Prices(PriceGuide(new_prices), PriceGuide(used_prices))

    def get_set_prices(self, lego_set: LegoSet) -> PriceGuide:
        new_prices = self.cached("prices_new", timedelta(weeks=1), lego_set.no, self.client.catalog.getPriceGuide,
                                 'SET', lego_set.no, None, None, 'N', 'Y')
        used_prices = self.cached("prices_used", timedelta(weeks=1), lego_set.no, self.client.catalog.getPriceGuide,
                                  'SET', lego_set.no, None, None, 'U', 'Y')
        return Prices(PriceGuide(new_prices), PriceGuide(used_prices))


def get_order(orderno: str):
    with open("bricklink-token.json", "r") as fp:
        key_info = json.load(fp)
    client = api.ApiClient(consumer_key=key_info['consumer']['key'],
                           consumer_secret=key_info['consumer']['secret'],
                           access_token=key_info['access']['key'],
                           access_token_secret=key_info['access']['secret'])
    order_info = client.orders.getOrder(orderno)
    order_items = client.orders.getOrderItems(orderno)
    pprint(order_info)
    pprint(order_items)
