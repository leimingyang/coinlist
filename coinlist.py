#!/bin/usr/python


import sys
import pprint
import requests


# ---------------------------------------------------------------------------
def fetch_coinlist():
    url = "https://api.coinmarketcap.com/v1/ticker/"
    params = {'limit': 0}

    r = requests.get(url, params=params)
    if r.status_code != requests.codes.ok:
        sys.exit('fetch failed.')

    try:
        coin_list = r.json()
    except ValueError:
        sys.exit('json parsing error.')

    return [(coin['name'], coin['symbol']) for coin in coin_list]


# ---------------------------------------------------------------------------
coinlist = fetch_coinlist()
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(coinlist)
pp.pprint(len(coinlist))
