#!/usr/bin/python


import os
import sys
import json
import pprint
import argparse
import requests


# ---------------------------------------------------------------------------
coinlist_path = "coinlist"


# ---------------------------------------------------------------------------
def fetch_coinlist():
    global coinlist_path

    url = "https://api.coinmarketcap.com/v1/ticker/"
    params = {'limit': 0}

    r = requests.get(url, params=params)
    if r.status_code != requests.codes.ok:
        sys.exit('fetch failed.')

    try:
        coin_list = r.json()
    except ValueError:
        sys.exit('json parsing error.')

    with open(coinlist_path, 'w') as g:
        json.dump([{'name': coin['name'], 'symbol': coin['symbol']} for coin in coin_list],
                  g, indent=4)


# ---------------------------------------------------------------------------
def get_coinlist():
    global coinlist_path

    if not os.path.exists(coinlist_path):
        fetch_coinlist()

    with open(coinlist_path) as f:
        cl = json.load(f)

    return cl


# ---------------------------------------------------------------------------
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--fetch", help="do fetch", action="store_true")
    return parser.parse_args()


# ---------------------------------------------------------------------------
args = parse_arguments()
if args.fetch:
    fetch_coinlist()
coinlist = get_coinlist()
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(coinlist)
pp.pprint(len(coinlist))
