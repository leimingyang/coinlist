import os
import sys
import json
import time
import pprint
import argparse
from operator import itemgetter
from urllib.parse import urlparse
from github import Github, GithubException


# ---------------------------------------------------------------------------
# globals
pp = pprint.PrettyPrinter(indent=4)

with open('credential') as f:
    credential = json.load(f)
github = Github(credential['username'], credential['password'])

coinlist_path = "coinlist"
source_info_path = "source_info"
repo_path = "repos"
good_repo_path = "good_repos"
best_repo_path = "best_repos"


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
                result = github.get_organization(paths[0])
            except GithubException:
                sys.exit('Organization not found')

            source_info[coin_symbol]['org'] = result.raw_data

        with open(source_info_path, 'w') as g:
            json.dump(source_info, g, indent=4)

        # break


# ---------------------------------------------------------------------------
def get_repos_current():
    global repo_path

    repos = {}
    if os.path.exists(repo_path):
        with open(repo_path) as f:
            repos = json.load(f)

    return repos


# ---------------------------------------------------------------------------
def fetch_repos(to_fresh):
    global pp
    global github
    global repo_path

    source_info = get_source_info_current()
    # print(len(source_info))

    repo_d = get_repos_current()
    for coin_symbol in source_info:
        name = source_info[coin_symbol]['name']
        # pp.pprint(source_info[coin_symbol])

        if 'org' in source_info[coin_symbol]:
            org = source_info[coin_symbol]['org']
            public_repos = org['public_repos']
            if not to_fresh and coin_symbol in repo_d:
                if public_repos == len(repo_d[coin_symbol]['repos']):
                    continue
            try:
                repos = github.get_user(org['login']).get_repos()
            except GithubException as e:
                print('exception: %s' % name)
                pp.pprint(e)
                continue

        elif 'user' in source_info[coin_symbol]:
            user = source_info[coin_symbol]['user']
            public_repos = user['public_repos']
            if not to_fresh and coin_symbol in repo_d:
                if public_repos == len(repo_d[coin_symbol]['repos']):
                    continue
            try:
                repos = github.get_user(user['login']).get_repos()
            except GithubException as e:
                print('exception: %s' % name)
                pp.pprint(e)
                continue
        else:
            print('repo not found: %s' % coin_symbol)
            continue

        if github.rate_limiting[0] == 0:
            print('sleeping for one hour ...')
            time.sleep(3600)

        print(name)

        repo_d[coin_symbol] = {'name': name, 'repos': []}
        for repo in repos:
            try:
                repo_raw = repo.raw_data
            except GithubException as e:
                print('exception: %s' % name)
                pp.pprint(e)
                continue

            print("\t%s" % repo_raw['name'])
            repo_data = {
                'name': repo_raw['name'],
                'description': repo_raw['description'],
                'html_url': repo_raw['html_url'],
                'size': repo_raw['size'],
                'language': repo_raw['language'],
                'subscribers_count': repo_raw['subscribers_count'],
                'stargazers_count': repo_raw['stargazers_count'],
                'forks_count': repo_raw['forks_count'],
                'created_at': repo_raw['created_at'],
                'pushed_at': repo_raw['pushed_at'],
                'updated_at': repo_raw['updated_at'],
                'open_issues_count': repo_raw['open_issues_count'],
            }
            if repo_raw['license']:
                repo_data['license'] = repo_raw['license']['key']
            if 'parent' in repo_raw:
                repo_data['parent'] = repo_raw['parent']['full_name']

            repo_d[coin_symbol]['repos'].append(repo_data)

            with open(repo_path, 'w') as g:
                json.dump(repo_d, g, indent=2)


# ---------------------------------------------------------------------------
def insert_repos(repos, r, total):
    if not repos:
        repos.append(r)
        return

    x = -1
    for i, repo in enumerate(repos):
        if total >= (repo['subscribers_count'] +
                     repo['stargazers_count'] + repo['forks_count']):
            x = i
            break

    if x == -1:
        repos.append(r)
    else:
        repos.insert(x, r)


# ---------------------------------------------------------------------------
def get_good_repos():
    global good_repo_path
    global best_repo_path

    all_repos = get_repos_current()
    good_repos_dict = {}
    best_repos_list = []
    for coin_symbol in all_repos:
        name = all_repos[coin_symbol]['name']
        repos = all_repos[coin_symbol]['repos']
        good_repos = []
        best_repos = []
        max_total = 0
        for r in repos:
            # if 'parent' in r:
            #     continue

            subscribers = r['subscribers_count']
            stargazers = r['stargazers_count']
            forks = r['forks_count']
            total = subscribers + stargazers + forks
            if total > max_total:
                max_total = total

            if subscribers >= 10 and stargazers >= 10 and forks >= 10:
                insert_repos(good_repos, r, total)

            if subscribers >= 100 or stargazers >= 100 or forks >= 100:
                insert_repos(best_repos, r, total)

        if good_repos:
            good_repos_dict[coin_symbol] = {'name': name}
            good_repos_dict[coin_symbol]['repos'] = good_repos

        if best_repos:
            best_repos_list.append((coin_symbol, name, best_repos, max_total))

    with open(good_repo_path, 'w') as g:
        json.dump(good_repos_dict, g, indent=2)

    best_repos_list.sort(key=itemgetter(3), reverse=True)
    best_repos_dict = {}
    for repo in best_repos_list:
        print(repo[1])
        best_repos_dict[repo[0]] = {'name': repo[1], 'repos': repo[2]}

    with open(best_repo_path, 'w') as g:
        json.dump(best_repos_dict, g, indent=2)


# ---------------------------------------------------------------------------
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="get source info",
                        action="store_true")
    parser.add_argument("-f", "--refresh", help="refresh source info",
                        action="store_true")
    parser.add_argument("-r", "--repos", help="get repos",
                        action="store_true")
    parser.add_argument("-g", "--good_repos", help="get good repos",
                        action="store_true")
    return parser.parse_args()


# ---------------------------------------------------------------------------
args = parse_arguments()
if args.source:
    fetch_source_info(args.refresh)
if args.repos:
    fetch_repos(args.refresh)
if args.good_repos:
    get_good_repos()
