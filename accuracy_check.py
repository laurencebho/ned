'''

get all links and 'link text' from a given wikipedia article.

Then for the entity mentions identified by the program that match the link text,
check how many disambiguate to the correct link

This produces the accuracy metric

you run it like:

python accuracy_check.py title filename

where title is the article title and filename is the json file output by CoreNLP

'''
import re
import sys


from wiki import generate_links_dict, get_wikitext
from ppr import ned
from cnlp_utils import get_entities
import settings

def find_wikitext_links(wikitext):
    '''
    parses some wikitext and exracts the links from it, then
    returns a dict of (link text:link title) pairs

    :param wikitext: a string of wikitext (the rich text
    of a wikipedia article)
    '''
    pattern = re.compile(r'\[\[([^\[\]]*)\]\]')
    links = re.findall(pattern, wikitext)

    wikipedia_dict = {} #pretty raw but this is ok
    for link in links:
        parts = link.split('|') #split into link title and link text
        num_parts = len(parts)
        if num_parts == 2:
            wikipedia_dict[parts[1]] = parts[0]
        elif num_parts == 1:
            wikipedia_dict[parts[0]] = parts[0]
    return wikipedia_dict


def calculate_accuracy(wikipedia_dict, disambiguations_dict):
    '''
    calculates percentage accuracy of a proposed disambiguation for
    a set of entity mentions of a Wikipedia article

    :param wikipedia_dict: the truthset dict
    :param disambiguations_dict: the dict of proposed
    disambiguations
    '''
    correct, total = 0, 0
    for mention, disambiguation in disambiguations_dict.items():
        if mention in wikipedia_dict:
            if wikipedia_dict[mention] == disambiguation:
                correct += 1
            total += 1
    if total == 0:
        return 0
    return 100 * correct / total


def main():
    settings.init('en')
    wikitext = get_wikitext(sys.argv[1])
    wiki_dict = find_wikitext_links(wikitext)
    entities = get_entities(sys.argv[2])
    disambiguations = ned(entities)
    accuracy = calculate_accuracy(wiki_dict, disambiguations)
    settings.logger.info(f'Accuracy on article "{sys.argv[1]}": {accuracy}%')


if __name__ == '__main__':
    main()