import requests
import json
import os

def login(username, password):
    login_info = {'user': username, 'passwd': password, 'api_type':'json'}
    headers = {'user-agent': 'Gif Exploder Bot by /u/kuzux, explodes animated gifs. boom.', }
    client = requests.session()
    client.headers = headers
    req = client.post('http://www.reddit.com/api/login', data=login_info)
    res = json.loads(req.content)

    if res['json']['errors'] != []:
        raise Exception(res['json']['errors'][0])

    return res['json']['data']

print login('GifExploderBot', os.environ['GIFEXPLODERBOT_PASSWORD'])
