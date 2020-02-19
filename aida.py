import csv
import re
import pprint


from ppr import ned
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
            if f'http://en.wikipedia.org/wiki/{title}' == truthset[mention]:
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
        settings.logger.info(f'accuracy for {doc}: {percentage}%')
        grand_correct += correct
        grand_total += total
    
    final_percentage = 100 * grand_correct / grand_total
    print(f'overall accuracy: {final_percentage}%')


def main():
    settings.init()
    test_performance()


if __name__ == '__main__':
    main()