'''
script that runs on a text file in the wikipedia dataset,
and fetches text of all articles listed

run like:
./from_title_list.py path/to/titles.txt path/to/saved language
'''

import requests
import sys

url = f'https://{sys.argv[3]}.wikipedia.org/w/api.php'
filename = sys.argv[1]
savedir = sys.argv[2]

with open(filename) as fr:
    for line in fr.readlines():
        line = line.rstrip()
        params = {
            'action': 'query',
            'format': 'json',
            'titles': line,
            'prop': 'extracts',
            'exIntro': '',
            'explaintext': ''
        }

        data = requests.get(url=url, params=params).json()
        page = next(iter(data['query']['pages'].values()))
        text = page['extract']
        savefile = f'{savedir}/{line.replace(" ", "_")}.txt' #save with underscores in name
        with open(savefile, 'w') as fw:
            fw.write(text)