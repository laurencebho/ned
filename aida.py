import csv
import re
import pprint
from concurrent.futures import ThreadPoolExecutor, as_completed

from ppr import ned, build_graph, analyse_graph
import settings


def extract_docname(s):
    pattern = re.compile(r'\((.*)\)')
    return re.findall(pattern, s)[0]


def create_aida_dict():
    with open('aida_annotations.tsv') as fr:
        reader = csv.reader(fr, delimiter='\t')
        
        docs = {}
        docname = ''
        for row in reader:
            #print(row, ' ::: ', len(row))
            if len(row) == 1:
                if '-DOCSTART-' in row[0]:
                    docname = extract_docname(row[0])
                    docs[docname] = {}
            elif len(row) == 5:
                if row[1] not in docs[docname]:
                    docs[docname][row[1]] = row[2]
    return docs


def count_correct(truthset, testset):
    correct, total = 0, 0
    for mention, title in testset.items():
        if mention in truthset:
            if 'http://en.wikipedia.org/wiki/{0}'.format(title) == truthset[mention]:
                correct += 1
            total += 1
    return correct, total


def test_performance():
    grand_correct, grand_total = 0, 0
    aida_dict = create_aida_dict()
    for doc in aida_dict:
        entities = list(aida_dict[doc].keys())
        disambiguations = ned(entities)
        data = pprint.pformat(disambiguations)
        settings.logger.info(data)
        correct, total = count_correct(aida_dict[doc], disambiguations)
        percentage = 100 * correct / total
        settings.logger.info('accuracy for {0}: {1}%'.format(doc, percentage))
        grand_correct += correct
        grand_total += total
    
    final_percentage = 100 * grand_correct / grand_total
    print('overall accuracy: {0}%'.format(final_percentage))
    

def test_performance_parallel():
    settings.PARALLEL = True
    grand_correct, grand_total = 0, 0
    aida_dict = create_aida_dict()
    with ThreadPoolExecutor(max_workers=4) as e:
        doc_ents = []
        for doc_name, d in aida_dict.items():
            doc_ents.append((doc_name, list(d.keys())))
        futures_dict = {e.submit(build_graph, ents) : doc_name for doc_name, ents in doc_ents}
        for future in as_completed(futures_dict):
            doc_name = futures_dict[future]
            G, links_dict, backlinks_count_dict = future.result()

            #perform the more computationally intense step not in parallel
            disambiguations = analyse_graph(G, links_dict, backlinks_count_dict)
            correct, total = count_correct(aida_dict[doc_name], disambiguations)
            print('{0} has {1} total terms of which {2} are correct'.format(doc_name, total, correct))
            percentage = 100 * correct / total
            settings.logger.info('accuracy for {0}: {1}%'.format(doc_name, percentage))
            grand_correct += correct
            grand_total += total
            print('another one')
    
    final_percentage = 100 * grand_correct / grand_total
    print('overall accuracy: {0}%'.format(final_percentage))


def disambiguate(doc):
    '''
    deprecated as a function
    '''
    entities = list(doc.keys())
    disambiguations = ned(entities)
    correct, total = count_correct(doc, disambiguations)
    percentage = 100 * correct / total
    settings.logger.info('accuracy for {0}: {1}%'.format(doc, percentage))
    return correct, total


def main():
    settings.init('en', False)
    test_performance_parallel()


if __name__ == '__main__':
    main()