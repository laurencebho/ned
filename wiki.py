import requests

from wikidata.client import Client
import mwclient


def make_mw_request(params):
    '''
    make a request to the MediaWiki API
    '''
    session = requests.Session()
    url = 'https://en.wikipedia.org/w/api.php'
    r = session.get(url=url, params=params)
    return r.json()


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