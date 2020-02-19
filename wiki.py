import requests
import os.path as op

from wikidata.client import Client
import mwclient

import settings


def make_mw_request(params):
    '''
    make a request to the MediaWiki API
    '''
    url = 'https://en.wikipedia.org/w/api.php'
    r = requests.get(url=url, params=params)
    return r.json()


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
        f'{title}/'
        'monthly/'
        f'{settings.date_handler.start}/'
        f'{settings.date_handler.end}'
    )
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
            return 'there seems to be a tie'


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


def check_disambiguation_page(title):
    '''
    determine if a title has an associated disambiguation page
    '''
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'links',
        'titles': f'{title} (disambiguation)',
        'pllimit': '500'
    }
    data = make_mw_request(params)
    pages = data['query']['pages']

    candidates = []
    target_phrase = title.lower()
    for page in pages.values():
        if 'missing' in page: #if not a valid disambiguation page
            return None
        links = page['links']
        for link in links:
            link_title = link['title'].lower()
            if target_phrase in link_title:
                if 'disambiguation' not in link_title:
                    candidates.append(link['title'])
    return candidates


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
    disamb_candidates = check_disambiguation_page(title)
    if disamb_candidates is not None:
        return disamb_candidates
    redirect = get_redirect(title)
    if redirect is not None:
        return [redirect]
    exact_match = check_exact_match(title)
    if exact_match:
        return [title]


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