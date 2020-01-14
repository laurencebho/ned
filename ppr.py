import networkx as nx
from matplotlib import pyplot as plt
import pprint

from wiki import get_candidates, edge_between, find_most_linked

def add_candidates(title, candidates, G):
    for candidate in candidates:
        G.add_node(G.number_of_nodes(), mention=title, candidate=candidate)


def add_edges(G):
    for u in G.nodes():
        for v in G.nodes():
            if G.nodes[u]['mention'] != G.nodes[v]['mention']:
                if not G.has_edge(u, v):
                    if edge_between(G.nodes[u]['candidate'], G.nodes[v]['candidate']):
                        G.add_edge(u, v)


def ppr(G):
    personalization = {}
    for node in G.nodes():
        personalization[node] = 1
    ppr = nx.pagerank(G, alpha=0.85, personalization=personalization)
    return ppr


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


if __name__ == '__main__':
    G = nx.Graph()
    add_candidates('Lincoln', ('Abraham Lincoln', 'Lincoln, England', 'Lincoln, Nebraska'), G)
    add_candidates('Civil War', ('American Civil War', 'Spanish Civil War', 'Civil War'), G)
    add_edges(G)

    ppr_scores = ppr(G)
    results = collect_results(G, ppr_scores)
    disambiguations = get_disambiguations(results)
    disambiguations = resolve_ties(disambiguations)

    pprint.pprint(disambiguations)

    '''
    #display the graph
    nx.draw_networkx(G, pos=nx.circular_layout(G), with_labels=True)	
    plt.show()
    '''
