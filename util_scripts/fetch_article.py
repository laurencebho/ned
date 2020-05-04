'''
a simple script to take a title of an article, fetch the text from Wikipedia, and save it as a text file

run like: python fetch_article.py title savedir lang
'''

import requests
import sys

url = 'https://{0}.wikipedia.org/w/api.php'.format(sys.argv[3])
params = {
    'action': 'query',
    'format': 'json',
    'titles': sys.argv[1],
    'prop': 'extracts',
    'exIntro': '',
    'explaintext': ''
}

data = requests.get(url=url, params=params).json()
page = next(iter(data['query']['pages'].values()))
text = page['extract']
filename = sys.argv[1].replace(' ', '_') + '.txt'
with open(f'{0}/{1}'.format(sys.argv[2], filename), 'w') as fw:
    fw.write(text)