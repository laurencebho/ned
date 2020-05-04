import requests
import os.path as op
import vcr
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re

import settings

def cache_request(filepath, params, response):
    if op.isfile(filepath):
        with open(filepath, 'r') as fr:
            all_reqs = json.load(fr)
            all_reqs[json.dumps(params)] = response
        with open(filepath, 'w') as fw:
            json.dump(all_reqs, fw)
    else:
        all_reqs = {json.dumps(params): response}
        with open(filepath, 'w') as fw:
            json.dump(all_reqs, fw)

    
def retrieve_response(filepath, params):
    with open(filepath, 'r') as fr:
        all_reqs = json.load(fr)
    search_string = json.dumps(params)
    if search_string in all_reqs:
        return all_reqs[search_string]
    return None


def make_mw_request(params):
    savefile = 'fixtures/cached_requests/all.json'
    '''
    make a request to the MediaWiki API
    '''
    '''
    with settings.VCR.use_cassette('fixtures/cassettes/all.yaml'):
        url = f'https://{settings.LANG}.wikipedia.org/w/api.php'
        r = settings.SESSION.get(url=url, params=params)
        return r.json()
    '''
    url = 'https://{0}.wikipedia.org/w/api.php'.format(settings.LANG)
    if settings.REPLAYING:
        response = retrieve_response(savefile, params)
        if response is not None:
            return response
    response = settings.SESSION.get(url=url, params=params).json()
    if (not settings.REPLAYING) and (not settings.PARALLEL):
        cache_request(savefile, params, response)
    return response


def parallelise_requests(f, *args):
    results = {}
    with ThreadPoolExecutor(max_workers=10) as e:
        params = zip(args)
        futures_dict = {e.submit(f(*tup)) for tup in params}
        for future in as_completed(futures_dict):
            results[futures_dict[future[0]]] = future.result()
    return results


def get_pageviews(title):
    '''
    make a request to the Wikimedia API to get
    the pageviews of a page by title
    '''
    url=(
        'https://wikimedia.org/api/rest_v1/'
        'metrics/'
        'pageviews/'
        'per-article/'
        'en.wikipedia/'
        'all-access/'
        'all-agents/'
        '{0}/'
        'monthly/'
        '{1}/'
        '{2}'
    ).format(title, settings.date_handler.start, settings.date_handler.end)

    r = requests.get(url=url)
    data = r.json()
    monthly_views = data['items']
    prev_month_views = int(monthly_views[-1]['views'])
    return prev_month_views


def request_links(title, plcontinue=None):
    '''
    make a single request for a page's links

    :param title: the title of the page to get links for

    :param plcontinue: a reference for the API specifying
    the point down the page to continue returning links from
    '''
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'links',
        'pllimit': '500',
        'titles': title,
    }
    if plcontinue is not None:
        params['plcontinue'] = plcontinue
    data = make_mw_request(params)
    pages = data['query']['pages']
    links = []
    for _, page in pages.items():
        if 'links' in page:
            for link in page['links']:
                links.append(link['title'])
    if 'continue' in data:
        plcontinue = data['continue']['plcontinue']
    else:
        plcontinue = None
    return links, plcontinue


def generate_links_dict(titles):
    '''
    create a dictionary of title:list pairs
    where each list contains the titles of all
    links on a page

    :param titles: a list of article titles
    '''
    links_dict = {}
    for title in titles:
        links = [] #list of links for a single title
        plcontinue = None
        while True:
            new_links, plcontinue = request_links(title, plcontinue)
            links += new_links
            if plcontinue is None:
                break
        links_dict[title] = links
    return links_dict
        

def lookup_link(page_title, target_title, links_dict):
    '''
    determine if a page links to a target page using a
    dictionary of pages and their contained links.
    returns a boolean

    :param page_title: title of page
    :param target_title: title of the link to look
    for on the page
    :param links_dict: the dictionary to search
    '''
    return target_title in links_dict[page_title]


def check_edge(title1, title2, links_dict):
    '''
    determines whether to add an undirected edge between
    two pages

    :param title1: the title of the first page
    :param title2: the title of the second page
    :param links_dict: dictionary of pages and their
    contained links to use for lookup
    '''
    return lookup_link(title1, title2, links_dict) or lookup_link (title2, title1, links_dict)


def link_between(page_title, target_title):
    '''
    determines if there is a link on one page to
    another target page

    :param page_title: title of page
    :param target_title: title of the link to look
    for on the page
    '''
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'links',
        'titles': page_title,
        'pltitles': target_title
    }

    data = make_mw_request(params)
    pages = data['query']['pages']

    #expect a single page json to be returned
    #if there is a 'links' value containing the title return True
    for page in pages.values():
        if 'links' in page:
            for link in page['links']:
                if link['title'] == target_title:
                    return True
                return False
        return False


def edge_between(title1, title2):
    '''
    determines whether to add an undirected edge between
    two pages

    :param title1: the title of the first page
    :param title2: the title of the second page
    '''
    return link_between(title1, title2) or link_between (title2, title1)


def count_backlinks(title, blcontinue=None):
    '''
    count the number of pages that link to a page

    :param title: the title of the page
    :param blcontinue: the continuation marker from
    the previous query if it exists
    '''
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'backlinks',
        'bllimit': '500',
        'bltitle': title
    }
    if blcontinue is not None:
        params['blcontinue'] = blcontinue
    data = make_mw_request(params)
    count = len(data['query']['backlinks'])
    if 'continue' in data:
        blcontinue = data['continue']['blcontinue']
    else:
        blcontinue = None
    return count, blcontinue


def create_backlinks_count_dict(candidates):
    '''
    creates a dictionary of title:backlinks_count pairs

    :param candidates: a list of candidate titles
    '''
    backlinks_count_dict = {}
    for candidate in candidates:
        total = 0
        blcontinue = None
        while True:
            count, blcontinue = count_backlinks(candidate, blcontinue)
            print(count)
            if  blcontinue is None:
                print('done')
                break
            total += count
        backlinks_count_dict[candidate] = total
    return backlinks_count_dict


def compare_backlinks(title1, title2):
    '''
    return the title with the most backlinks
    '''
    t1_continue = None
    t2_continue = None

    while True:
        t1_count, t1_continue = count_backlinks(title1, t1_continue)
        t2_count, t2_continue = count_backlinks(title2, t2_continue)

        if t1_count > t2_count:
            return title1
        elif t2_count > t1_count:
            return title2
        elif t1_count == t2_count and t1_count < 500:
            return (title1, title2)


def find_most_linked(titles):
    '''
    find the title with the most backlinks from a list of titles

    :param titles: iterable of strings corresponding to Wikipedia
    article titles
    '''
    for i, _ in reversed(list(enumerate(titles))):
        if i > 0:
            winner = compare_backlinks(titles[i], titles[i-1])
            if winner == titles[i]:
                del titles[i-1]
            else:
                del titles[i]
    return titles[0]


def check_exact_match(title):
    '''
    check if there is a Wikipedia page
    exactly matching the title

    :param title: the title of the page to
    search for
    '''
    params = {
        'action': 'query',
        'format': 'json',
        'titles': title,
    }
    data = make_mw_request(params)
    pages = data['query']['pages']

    for page in pages.values():
        if 'missing' in page:
            return False
        return True


def is_disambiguation_page(title):
    valid_categories = (
        'Category:Disambiguation pages|'
        'Category:All article disambiguation pages|'
        'Categoría:Wikipedia:Desambiguación'
    )
    params = {
        'action': 'query',
        'format': 'json',
        'titles': title,
        'prop': 'categories',
        'clcategories': valid_categories
    }
    data = make_mw_request(params)
    pages = data['query']['pages']
    for page in pages.values():
        if 'categories' in page:
            return True
    return False


def is_disambiguation_page_old(title):
    '''
    check if the title itself is a disambiguation page
    '''
    try:
        wikitext = get_wikitext(title)
    except:
        return False
    pattern = re.compile(r'\{\{(Disambiguation|disambiguation).*\}\}')
    links = re.findall(pattern, wikitext)
    if len(links) > 0:
        return True
    return False


def check_disambiguation_page(title):
    '''
    determine if a title has an associated disambiguation page
    '''
    if is_disambiguation_page(title):
        matches_title = True
        search_title = title
    else:
        matches_title = False
        search_title = '{0} (disambiguation)'.format(title)

    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'links',
        'titles': search_title,
        'pllimit': '500'
    }
    data = make_mw_request(params)
    pages = data['query']['pages']

    candidates = []
    target_phrase = title.lower()
    for page in pages.values():
        if 'missing' in page: #if not a valid disambiguation page
            return None, matches_title
        links = page['links']
        for link in links:
            link_title = link['title'].lower()
            if target_phrase in link_title:
                if 'disambiguation' not in link_title:
                    candidates.append(link['title'])
    return candidates, matches_title


def get_redirect(title):
    '''
    check if a title redirects to another wikipedia page

    :param title: the title of the potentially redirected page
    '''
    params = {
        'action': 'query',
        'format': 'json',
        'redirects': '',
        'titles': title,
    }

    data = make_mw_request(params)

    if 'redirects' in data['query']:
        #returns title of page redirected to
        for redirect in data['query']['redirects']:
            return redirect['to']
    return None


def get_candidates(title):
    '''
    get a list of all candidates for a title

    :param title: a mention and potential article title
    '''
    all_candidates = []
    disamb_candidates, matches_title = check_disambiguation_page(title)
    if disamb_candidates is not None:
        all_candidates += disamb_candidates
    redirect = get_redirect(title)
    if redirect is not None:
        all_candidates +=  [redirect]
    elif not matches_title:
        exact_match = check_exact_match(title)
        if exact_match:
            if title not in all_candidates: #if not already in the disambiguation page
                all_candidates += [title]
    return all_candidates


def trim_candidates(candidates, lower_count, fraction, heuristic='pageviews'):
    '''
    use a popularity heuristic to rank candidates
    by popularity, then take a percentage of the
    most popular

    :param candidates: a list of article titles
    :param lower_count: min number of candidates to return
    :param fraction: threshold fraction
    :param heuristic: a string, either 'backlinks'
    or 'pageviews'
    '''
    if len(candidates) <= lower_count:
        return candidates
    else:
        threshold = int(max(lower_count, (fraction * len(candidates) // 1)))
        pageviews_dict = {}
        for i, candidate in enumerate(candidates):
            pageviews_dict[i] = get_pageviews(candidate)
        sorted_candidates = [k for k, v in sorted(pageviews_dict.items(), key=lambda item: item[1])]
        return sorted_candidates[:threshold]


def get_wikitext(title):
    '''
    get the wikitext of a page for parsing

    :param title: the title of the page to fetch
    '''
    params = {
        'action': 'parse',
        'format': 'json',
        'page': title,
        'prop': 'wikitext'
    }
    data = make_mw_request(params)
    return data['parse']['wikitext']['*']


def get_random_pages(n):
    '''
    get a number of random wikipedia page titles

    :param n: the number of titles to get
    '''
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'random',
        'rnlimit': str(n)
    }
    data = make_mw_request(params)
    titles = []
    for item in data['query']['random']:
        titles.append(item['title'])
    return titles


def get_interlang_titles(title, langs):
    '''
    get the other-languages titles of a given title

    :param title: original title (ususally in English)
    :param langs: iterable of languages to get titles for
    :return: dict of lang: title pairs
    '''
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'langlinks',
        'format': 'json'
    }
    data = make_mw_request(params)
    interlang_titles = {}
    for page in data['query']['pages'].values():
        if 'langlinks' in page:
            for d in page['langlinks']:
                if d['lang'] in langs:
                    interlang_titles[d['lang']] = d['*']

    return interlang_titles
