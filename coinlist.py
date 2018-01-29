import os
import sys
import json
import pprint
import argparse
import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# globals
pp = pprint.PrettyPrinter(indent=4)
coinlist_path = "coinlist"


# ---------------------------------------------------------------------------
def fetch_coinlist():
    global coinlist_path

    print('fetching ...')
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
        json.dump([{'id': coin['id'], 'name': coin['name'], 'symbol': coin['symbol']} for coin in coin_list],
                  g, indent=4)


# ---------------------------------------------------------------------------
def add_info():
    global pp
    global coinlist_path

    print('adding info ...')
    if not os.path.exists(coinlist_path):
        fetch_coinlist()

    with open(coinlist_path) as f:
        cl = json.load(f)

    total = len(cl)
    count = 0
    for coin in cl:
        count += 1

        if 'website' in coin and 'source_code' in coin:
            continue

        print("%s (%d/%d)" % (coin['name'], count, total))

        id = coin['id']
        url = "https://coinmarketcap.com/currencies/%s" % id
        r = requests.get(url)
        if r.status_code != requests.codes.ok:
            sys.exit('add info failed.')

        soup = BeautifulSoup(r.content, 'html5lib')

        if 'website' not in coin:
            span = soup.find('span', class_='glyphicon glyphicon-link text-gray')
            if span:
                a = span.parent.find('a')
                coin['website'] = a['href']
            else:
                coin['website'] = ''

        if 'source_code' not in coin:
            span = soup.find('span', class_='glyphicon glyphicon-hdd text-gray')
            if span:
                a = span.parent.find('a')
                coin['source_code'] = a['href']
            else:
                coin['source_code'] = ''

        with open(coinlist_path, 'w') as g:
            json.dump(cl, g, indent=4)


# ---------------------------------------------------------------------------
def get_coinlist():
    global coinlist_path

    if not os.path.exists(coinlist_path):
        fetch_coinlist()

    with open(coinlist_path) as f:
        cl = json.load(f)

    if 'website' in cl[0] and 'source_code' in cl[0]:
        return cl

    add_info()
    with open(coinlist_path) as f:
        cl = json.load(f)

    return cl


# ---------------------------------------------------------------------------
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--fetch", help="do fetch", action="store_true")
    parser.add_argument("-a", "--add", help="add more info", action="store_true")
    return parser.parse_args()


# ---------------------------------------------------------------------------
args = parse_arguments()
if args.fetch:
    fetch_coinlist()
if args.add:
    add_info()
coinlist = get_coinlist()
pp.pprint(coinlist)
pp.pprint(len(coinlist))
