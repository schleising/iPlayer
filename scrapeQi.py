import re
import subprocess

import requests

BASEURL = 'https://www.bbc.co.uk'

regex = re.compile(r'"/iplayer/episode/[a-z0-9]+/qi-series-[a-z]-[0-9]+-[a-zA-Z- ]+"')

seriesUrls = [
    'https://www.bbc.co.uk/iplayer/episodes/b006ml0g/qi?seriesId=b006ml0f',
    'https://www.bbc.co.uk/iplayer/episodes/b006ml0g/qi?seriesId=b0080kf3',
]

for seriesUrl in seriesUrls:
    page = requests.get(seriesUrl)

    if page.status_code == requests.codes.OK:
        results = regex.findall(page.text)
        exts = [result.replace('"', '') for result in results]

        urls = sorted({f'{BASEURL}{ext}' for ext in exts}, key=lambda x: x.split(r'/')[-1])

        for url in urls:
            print(url)
            subprocess.run(['youtube-dl', url])
