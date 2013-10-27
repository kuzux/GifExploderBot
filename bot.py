# -*- coding: utf-8 -*-

import requests
import json
import os
import mimetypes

def login(username, password):
    login_info = {'user': username, 'passwd': password, 'api_type':'json'}
    headers = {'user-agent': 'Gif Exploder Bot by /u/kuzux, explodes animated gifs. boom.', }
    client = requests.session()
    client.headers = headers
    req = client.post('http://www.reddit.com/api/login', data=login_info)
    res = json.loads(req.content)

    if res['json']['errors'] != []:
        raise Exception(res['json']['errors'][0])

    client.modhash = res['json']['data']['modhash']
    client.user = username
    client.headers['X-Modhash']=client.modhash

    return client

def new_stories(client, subreddit):
    params = {'limit': 100,}
    url = "http://www.reddit.com/r/{sr}/new.json".format(sr=subreddit)
    req = client.get(url, params=params)
    res = json.loads(req.text)
    return res['data']['children']

client = login('GifExploderBot', os.environ['GIFEXPLODERBOT_PASSWORD'])
stories = new_stories(client, 'MapPorn')

for story in stories:
    mimetype = mimetypes.guess_type(story['data']['url'])[0]
    if mimetype == "image/gif":
        print "{n}: {u}".format(n=story['data']['title'].encode('utf-8'), u=story['data']['url'])
