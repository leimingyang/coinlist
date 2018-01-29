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
def get_coin_list_current():
    global coinlist_path

    coindict = {}
    if os.path.exists(coinlist_path):
        with open(coinlist_path) as f:
            coindict = json.load(f)

    return coindict


# ---------------------------------------------------------------------------
def fetch_detail(coin_id):
    print(coin_id)

    url = "https://coinmarketcap.com/currencies/%s" % coin_id
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        sys.exit('fetch detail failed: %s' % coin_id)

    soup = BeautifulSoup(r.content, 'html5lib')

    span = soup.find('span', class_='glyphicon glyphicon-link text-gray')
    if span:
        a = span.parent.find('a')
        website = a['href']
    else:
        website = ''

    span = soup.find('span', class_='glyphicon glyphicon-hdd text-gray')
    if span:
        a = span.parent.find('a')
        source_code = a['href']
    else:
        source_code = ''

    return website, source_code


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
        coin_list_new = r.json()
    except ValueError:
        sys.exit('json parsing error.')

    coindict = get_coin_list_current()
    for coin in coin_list_new:
        coin_id = coin['id']

        if coin_id in coindict:
            coindict[coin_id]['last_updated'] = coin['last_updated']
            coindict[coin_id]['rank'] = coin['rank']
            if coindict[coin_id]['website'] == '' or coindict[coin_id]['source_code'] == '':
                website, source_code = fetch_detail(coin_id)
                if website != coindict[coin_id]['website']:
                    coindict[coin_id]['website'] = website
                if source_code != coindict[coin_id]['source_code']:
                    coindict[coin_id]['source_code'] = source_code
        else:
            website, source_code = fetch_detail(coin_id)
            coindict[coin_id] = {'name': coin['name'],
                                 'symbol': coin['symbol'],
                                 'rank': coin['rank'],
                                 'last_updated': coin['last_updated'],
                                 'website': website,
                                 'source_code': source_code}

        with open(coinlist_path, 'w') as g:
            json.dump(coindict, g, indent=4)


# ---------------------------------------------------------------------------
def get_coinlist():
    global coinlist_path

    if not os.path.exists(coinlist_path):
        sys.exit('coinlist path not found')

    with open(coinlist_path) as f:
        coin_d = json.load(f)

    return coin_d


# ---------------------------------------------------------------------------
def parse_info(cl):
    no_website = 0
    no_source = 0
    for coin_id in cl:
        if not cl[coin_id]['website']:
            no_website += 1
        if not cl[coin_id]['source_code']:
            no_source += 1

    print('no website: %d' % no_website)
    print('no_source: %d' % no_source)


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
parse_info(coinlist)
