from ..lib.brick import Color, Dimensions, Image, Part, LegoSet, Brick, BrickCollection, BrickPile
from .bricklink import api
from pprint import pformat, pprint
from datetime import datetime, timedelta
import html
import os.path
import json
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

    def cached(self, subdir: str, ident: str, fn: callable, *args):
        cache_file = os.path.join(self.cache_directory, subdir, ident)
        if os.path.exists(cache_file):
            with open(cache_file, "r") as fp:
                data = json.load(fp)
            return data
        out = fn(*args)
        with open(cache_file, "w+") as fp:
            json.dump(out, fp)
        return out

    def get_part(self, no: str):
        log.debug("fetching part number: {}".format(no))
        data = self.cached("parts", no, self.client.catalog.getItem, "PART", no)
        assert data['no'] == no, pformat(data)
        assert data['type'] == 'PART', pformat(data)
        dim = Dimensions(data['dim_x'], data['dim_y'], data['dim_z'], data['weight'])
        img = Image(data['image_url'], data['thumbnail_url'])
        return Part(no, data['name'], data['category_id'], dim, img, data['is_obsolete'], data['year_released'])

    def get_color(self, ident: int):
        log.debug("fetching color id: {}".format(ident))
        data = self.cached("color", str(ident), self.client.color.getColorDetail, ident)
        return Color(ident, data['color_name'], data['color_code'], data['color_type'])

    def get_set(self, no: str):
        data = self.cached("set_info", no, self.client.catalog.getItem, 'SET', no)
        assert data['type'] == 'SET'
        dim = Dimensions(data['dim_x'], data['dim_y'], data['dim_z'], data['weight'])
        img = Image(data['image_url'], data['thumbnail_url'])
        lego_set = LegoSet(no, data['name'], data['category_id'], dim, img, data['is_obsolete'], data['year_released'])
        item_data = self.cached("set_items", no, self.client.catalog.getSubsets, 'SET', no)
        for entry in item_data:
            for item in entry['entries']:
                # Load the part.
                if item['item']['type'] != 'PART':
                    log.warning("Unrecognized item type in set: {}".format(item['item']['type']))
                part = self.get_part(item['item']['no'])

                # Load the color.
                color = Color.none()
                if item['color_id'] != 0:
                    color = self.get_color(item['color_id'])

                # Query all LEGO element_ids that this part/color has been released as.
                element_ids = []
                elements = self.cached("element_id", part.no + '-' + str(color.id),
                                       self.client.item_mapping.getElementID, part.no, color.id)
                if not elements:
                    elements = self.cached("element_id", part.no,
                                           self.client.item_mapping.getElementID, part.no)
                for element in elements:
                    element_ids.append(element['element_id'])

                extras = item['extra_quantity']
                quantity = item['quantity'] + extras
                # TODO: what are is_alternate and is_counterpart?
                brick = Brick(part, color, element_ids)
                lego_set.add_brick_pile(BrickPile(quantity, extras, brick))

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


def get_order(orderno: str) -> BrickCollection:
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
