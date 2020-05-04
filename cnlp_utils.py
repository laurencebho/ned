import json


##NOTE : MODIFY THIS TO ONLY HAVE LOCATION, PERSON, ORGANIZATION (look in the json files for details)


def get_entities(filename):
    '''
    opens a json file produced by CoreNLP and
    reads the named entities from it

    :param filename: the name of the json file
    to open
    '''
    entities = set()
    with open(filename) as fr:
        sentences = json.load(fr)['sentences']
        for sentence in sentences:
            for mention in sentence['entitymentions']:
                if mention['ner'] in ['PERSON', 'NATIONALITY', 'ORGANIZATION', 'LOCATION']:
                    entities.add(mention['text'])
    
    return entities
