import networkx as nx
import numpy as np
from matplotlib import pyplot as plt
import pprint
import argparse
import json

from wiki import (get_candidates, edge_between, find_most_linked,
generate_links_dict, check_edge, get_pageviews, trim_candidates,
create_backlinks_count_dict, parallelise_requests)
import settings

from cnlp_utils import get_entities

def add_candidates(title, candidates, G):
    for candidate in candidates:
        G.add_node(G.number_of_nodes(), mention=title, candidate=candidate)


def add_edges_uncached(G):
    for u in G.nodes():
        for v in G.nodes():
            if G.nodes[u]['mention'] != G.nodes[v]['mention']:
                if not G.has_edge(u, v):
                    if edge_between(G.nodes[u]['candidate'], G.nodes[v]['candidate']):
                        G.add_edge(u, v)


def add_edges(G, titles, links_dict):
    for u in G.nodes():    
        for v in G.nodes():
            if G.nodes[u]['mention'] != G.nodes[v]['mention']:
                if check_edge(G.nodes[u]['candidate'], G.nodes[v]['candidate'], links_dict):
                    G.add_edge(u, v)
    

def ppr(G):
    personalization = {}
    for node in G.nodes():
        personalization[node] = 1
    ppr = nx.pagerank(G, alpha=0.85, personalization=personalization)
    return ppr


def manual_ppr(G, iterations, d):
    #adjacency matrix
    M = nx.to_numpy_matrix(G)
    #normalise M so each column
    #sums to 1
    for j in range(M.shape[1]):
        col = M[:,j]
        if col.any():
            col = col / np.linalg.norm(col, 1)
        M[:,j] = col

    #final scores matrix
    S = np.zeros(M.shape)

    n = M.shape[0]

    for i in range(n):
        #the vector of scores
        v = np.full((n, 1), 1/n)
        p = np.zeros((n, 1))
        p[i][0] = 1.0
        for _ in range(iterations):
            #personalisation vector
            v = ((d * M) @ v) + (1 - d) * p
        v.shape = n
        S[:,i] = v[:]
    
    return G, S


def compute_final_scores_pageviews(G, S):
    n = S.shape[0]

    pageviews = []
    for i in range(n):
        pageviews.append(get_pageviews(G.nodes[i]['candidate']))
    for i in range(n):
        mention_max_scores = {}
        u = G.nodes[i]
        for j in range(n):
            if i != j:
                v = G.nodes[j]
                mention = v['mention']
                if mention != u['mention']:
                    score = S[i, j] * pageviews[j]
                    if mention not in mention_max_scores or score > mention_max_scores[mention][1]:
                        mention_max_scores[mention] = (v['candidate'], score)
        u['score'] = sum([val[1] for val in mention_max_scores.values()])



def compute_final_scores(G, S, links_dict, backlinks_count_dict):
    n = S.shape[0]

    for i in range(n):
        mention_max_scores = {}
        u = G.nodes[i]
        for j in range(n):
            if i != j:
                v = G.nodes[j]
                mention = v['mention']
                if mention != u['mention']:
                    #multiply by the count of the backlinks
                    score = S[i, j] #* (backlinks_count_dict[v['candidate']]) #+ len(links_dict[v['candidate']]))
                    if mention not in mention_max_scores or score > mention_max_scores[mention][1]:
                        mention_max_scores[mention] = (v['candidate'], score)
        u['score'] = sum([val[1] for val in mention_max_scores.values()])


def collect_results(G, ppr_scores):
    '''
    collect candidate scores for each mention

    :param G: the graph which has had the PPR algorithm applied to it

    :param ppr_scores: the output scores dict from the PPR algorithm
    '''
    mentions = {}
    for node in G.nodes():
        mention = G.nodes[node]['mention']
        candidate = G.nodes[node]['candidate']
        if mention not in mentions:
            mentions[mention] = {}
        mentions[mention][candidate] = ppr_scores[node]
    return mentions


def get_disambiguations(mentions):
    disambiguations = {}
    for mention, candidates in mentions.items():
        best = 0
        best_candidates = []
        for candidate, score in candidates.items():
            #add some code here to compute the product with initial similarity
            if score > best:
                best = score
                best_candidates = [candidate]
            elif score == best:
                best_candidates.append(candidate)
        disambiguations[mention] = best_candidates
    return disambiguations


def resolve_ties(disambiguations):
    '''
    resolve any candidates with tied scores, and convert values
    from lists of candidates to strings
    '''
    for mention, candidates in disambiguations.items():
        if len(candidates) == 1: #convert from list of size 1 to string
            disambiguations[mention] = candidates[0]
        else:
            disambiguations[mention] = find_most_linked(candidates)
    return disambiguations


def build_graph(entities):
    '''
    this function is the same as the top part of the ned function
    '''
    all_candidates = []
    G = nx.Graph()
    total = 0
    for e in entities:
        candidates = get_candidates(e)
        #candidates = trim_candidates(candidates, 3, 0.4)
        if candidates is not None:
            settings.logger.info('adding candidates for {0}'.format(e))
            if settings.VERBOSE:
                for candidate in candidates:
                    settings.logger.info('  {0}'.format(candidate))
            all_candidates += candidates
            add_candidates(e, candidates, G)
            total += len(candidates)
    settings.logger.info('total nodes: {0}'.format(total))
    settings.logger.info('fetching links for all candidates')
    links_dict = generate_links_dict(all_candidates)
    #backlinks_count_dict = create_backlinks_count_dict(all_candidates)
    backlinks_count_dict = {}
    settings.logger.info('adding edges to knowledge graph')
    add_edges(G, all_candidates, links_dict)
    return G, links_dict, {}


def analyse_graph(G, links_dict, backlinks_count_dict):
    '''
    this function is the bottom part of the ned function
    '''
    G, S = manual_ppr(G, 20, 0.85)
    compute_final_scores(G, S, links_dict, backlinks_count_dict)
    disambiguations = collect_disambiguations(G)
    return disambiguations


def ned(entities):
    all_candidates = []
    G = nx.Graph()
    total = 0
    for e in entities:
        candidates = get_candidates(e)
        #candidates = trim_candidates(candidates, 3, 0.4)
        if candidates is not None:
            settings.logger.info('adding candidates for {0}'.format(e))
            if settings.VERBOSE:
                for candidate in candidates:
                    settings.logger.info('    {0}'.format(candidate))
            all_candidates += candidates
            add_candidates(e, candidates, G)
            total += len(candidates)
    settings.logger.info('total nodes: {0}'.format(total))
    settings.logger.info('fetching outgoing links for all candidate articles')
    links_dict = generate_links_dict(all_candidates)
    #backlinks_count_dict = create_backlinks_count_dict(all_candidates)
    backlinks_count_dict = {}
    settings.logger.info('adding edges to knowledge graph')
    add_edges(G, all_candidates, links_dict)
    if settings.VERBOSE:
        pos = nx.spring_layout(G)
        nx.draw(G, pos, node_size=20, font_size=8)
        plt.savefig('plots/knowledge_graph.png', format='PNG')

    settings.logger.info('running PPR on knowledge graph')
    G, S = manual_ppr(G, 20, 0.85)
    compute_final_scores(G, S, links_dict, backlinks_count_dict)
    disambiguations = collect_disambiguations(G)
    return disambiguations


def collect_disambiguations(G):
    settings.logger.info('aggregating final scores')
    disambiguations = {}
    scores = {}
    for i in G.nodes():
        u = G.nodes[i]
        if u['mention'] not in disambiguations or u['score'] > scores[u['mention']]:
                disambiguations[u['mention']] = u['candidate']
                scores[u['mention']] = u['score']
        elif scores[u['mention']] == u['score']: #resolve a tie
            disambiguations[u['mention']] = find_most_linked([disambiguations[u['mention']], u['candidate']])
    return disambiguations


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile',
        help='path to the input file (JSON, CSV or TSV) to extract entities from')
    parser.add_argument('outfile',
        help='path to the output JSON file to save disambiguations')
    parser.add_argument('-l', '--language', help='language', default='en')
    parser.add_argument('-r', '--replay', help='replay requests', action='store_true')
    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()
    settings.init(args.language, args.replay)

    entities = get_entities(args.infile)
    #get disambiguations and format them into a printable string
    disambiguations = pprint.pformat(ned(entities))
    settings.logger.info(disambiguations)
    with open(args.outfile, 'w') as fw:
        json.dump(disambiguations, fw)
    

if __name__ == '__main__':
    main()
    '''
    #display the graph
    nx.draw_networkx(G, pos=nx.circular_layout(G), with_labels=True)	
    plt.show()
    '''
