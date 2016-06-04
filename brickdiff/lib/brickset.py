from .brick import Brick
from .lego_set import LegoSet, LegoSetNotFound
import csv
import logging
import requests


log = logging.getLogger()


def get_set(setno: str) -> LegoSet:
    """
    Set number should be in a form like: 8460-1
    """
    log.debug("Querying brickset for set {}".format(setno))
    response = requests.get('http://www.brickset.com/export/inventory/?Set=' + setno)
    if len(response.text.split()) == 1:
        log.error("No set {} found at brickset".format(setno))
        raise LegoSetNotFound(setno)

    # Parse as csv
    lego_set = LegoSet(setno, 'brickset')
    csvreader = csv.reader(response.text.split())
    next(csvreader)  # skip header
    #SetNumber,PartID,Quantity,Colour,Category,DesignID,PartName,ImageURL,SetCount
    for row in csvreader:
        setno_part, bricksetid, count, color, category, partno, desc, imgurl, set_count = row
        bricksetid = int(bricksetid)
        count = int(count)
        img = "http://cache.lego.com/media/bricks/5/1/{}.jpg".format(bricksetid)
        partno = str(int(partno))
        lego_set.add_part(count, Brick(partno, color, desc, img))
    return lego_set


