from .brick import Brick
from .lego_set import LegoSet, LegoSetNotFound
from bs4 import BeautifulSoup
import logging
import requests


log = logging.getLogger()


def get_set(setno: str) -> LegoSet:
    """
    Set number should be in a form like: 8460-1
    """
    log.debug("Querying peeron for set {}".format(setno))
    response = requests.get('http://peeron.com/inv/sets/' + setno)
    if 'Your query resulted in no matches' in response.text:
        log.error("No set {} found at peeron".format(setno))
        raise LegoSetNotFound(setno)

    # Parse as html
    lego_set = LegoSet(setno, 'peeron')
    soup = BeautifulSoup(response.text, "html.parser")
    for tbl in soup.find_all('table'):
        if tbl.th is not None:
            for tr in tbl.find_all('tr'):
                tds = [td for td in tr.find_all('td')]
                if not tds:
                    continue
                cnt = tds[0].get_text()
                partno = tds[1].get_text()
                color = tds[2].get_text()
                desc = tds[3].get_text()
                try:
                    img = tds[4].a.img.get('src')
                except AttributeError:
                    img = ''  # sticker sheets mostly
                lego_set.add_part(int(cnt), Brick(partno, color, desc, img))
    return lego_set
