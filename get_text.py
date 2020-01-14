'''
a simple script to take a title of an article, fetch the text from Wikipedia, and save it as a text file
'''

import requests
import sys

url = 'https://en.wikipedia.org/w/api.php'
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
with open(filename, 'w') as fw:
    fw.write(text)