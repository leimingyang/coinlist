import os
import sys
import json
import pprint
import argparse
from urllib.parse import urlparse
from github import Github
from github import GithubException


# ---------------------------------------------------------------------------
# globals
pp = pprint.PrettyPrinter(indent=4)

with open('credential') as f:
    credential = json.load(f)
github = Github(credential['username'], credential['password'])

coinlist_path = "coinlist"
source_info_path = "source_info"


# ---------------------------------------------------------------------------
def get_coinlist():
    global coinlist_path

    if not os.path.exists(coinlist_path):
        sys.exit('coinlist path not found')

    with open(coinlist_path) as f:
        coin_d = json.load(f)

    return coin_d


# ---------------------------------------------------------------------------
def get_source_info_current():
    global source_info_path

    source_info = {}
    if os.path.exists(source_info_path):
        with open(source_info_path) as f:
            source_info = json.load(f)

    return source_info


# ---------------------------------------------------------------------------
def fetch_repos(user):
    global pp

    repos = []
    for repo in user.get_repos():
        repos.append(user.get_repo(repo.name).raw_data)

    # pp.pprint(repos)
    return repos


# ---------------------------------------------------------------------------
def fetch_source_info(to_fresh):
    global pp
    global github
    global source_info_path

    print('fetching ...')
    coin_d = get_coinlist()
    source_info = get_source_info_current()

    for coin_id in coin_d:
        if not to_fresh and coin_d[coin_id]['symbol'] in source_info:
            continue

        coin_name = coin_d[coin_id]['name']
        coin_symbol = coin_d[coin_id]['symbol']
        source_code_url = coin_d[coin_id]['source_code']
        if source_code_url.find('github.com') == -1:
            continue

        print(coin_id)

        parse_result = urlparse(source_code_url)
        url_path = parse_result.path
        if url_path.startswith('/'):
            url_path = url_path[1:]
        if url_path.endswith('/'):
            url_path = url_path[:-1]

        paths = url_path.split('/')
        len_paths = len(paths)
        # if len_paths < 1 or len_paths > 2:
        #     print(source_code_url)
        try:
            result = github.get_user(paths[0])
        except GithubException as e:
            print(source_code_url)
            pp.pprint(e)
            continue

        result_raw = result.raw_data

        source_info[coin_symbol] = {}
        source_info[coin_symbol]['name'] = coin_name
        source_info[coin_symbol]['source_code_site'] = '%s://%s' % (
            parse_result.scheme, parse_result.netloc)

        if result_raw['type'] == 'User':
            source_info[coin_symbol]['user'] = result_raw

        elif result_raw['type'] == 'Organization':
            try:
                result = github.get_user(paths[0])
            except GithubException:
                sys.exit('Organization not found')

            source_info[coin_symbol]['org'] = result.raw_data

        # repos = fetch_repos(result)
        # source_info[coin_symbol]['repos'] = repos

        with open(source_info_path, 'w') as g:
            json.dump(source_info, g, indent=4)

        # break


# ---------------------------------------------------------------------------
def get_source_info():
    global source_info_path

    if not os.path.exists(source_info_path):
        sys.exit('source_info path not found')

    with open(coinlist_path) as f:
        source_info = json.load(f)

    return source_info


# ---------------------------------------------------------------------------
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="get source info",
                        action="store_true")
    parser.add_argument("-r", "--refresh", help="refresh source info",
                        action="store_true")
    return parser.parse_args()


# ---------------------------------------------------------------------------
args = parse_arguments()
if args.source:
    fetch_source_info(args.refresh)
