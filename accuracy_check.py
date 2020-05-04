'''

get all links and 'link text' from a given wikipedia article.

Then for the entity mentions identified by the program that match the link text,
check how many disambiguate to the correct link

This produces the accuracy metric

you run it like:

python accuracy_check.py title filename lang

where title is the article title, filename is the json file output by CoreNLP
and lang is the language code

'''
import re
import sys
import argparse


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
    marked = [] #list of marked disambiguations
    correct, total = 0, 0
    for mention, disambiguation in disambiguations_dict.items():
        if mention in wikipedia_dict:
            if wikipedia_dict[mention] == disambiguation:
                marked.append([mention, disambiguation, wikipedia_dict[mention], 'Yes'])
                correct += 1
            else:
                marked.append([mention, disambiguation, wikipedia_dict[mention], 'No'])
            total += 1
    if total == 0:
        return 0, []
    return 100 * correct / total, marked


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--title',
        help='title of the Wikipedia article to parse')
    parser.add_argument('-f', '--infile',
        help='path to the JSON file output by CoreNLP')
    parser.add_argument('-l', '--language', help='language', default='en')
    parser.add_argument('-r', '--replay', help='replay requests', action='store_true')
    parser.add_argument('-v', '--verbose', help='verbose mode', action='store_true')
    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()
    settings.init(language=args.language, replaying=args.replay, verbose=args.verbose)
    wikitext = get_wikitext(args.title)
    wiki_dict = find_wikitext_links(wikitext)
    entities = get_entities(args.infile)
    disambiguations = ned(entities)
    accuracy, marked = calculate_accuracy(wiki_dict, disambiguations)
    print()
    print('Disambiguations')
    print('===============')
    print()
    for row in marked:
        s = 'Mention: {0}    Disambiguation: {1}    Wikipedia link: {2}    Correct: {3}'.format(row[0], row[1], row[2], row[3])
        if row[3] == 'Yes':
            settings.logger.warn(s)
        else: settings.logger.error(s)
    print()
    settings.logger.info('Accuracy on article "{0}": {1}%'.format(args.title, accuracy))


if __name__ == '__main__':
    main()