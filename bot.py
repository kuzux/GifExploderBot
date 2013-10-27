# -*- coding: utf-8 -*-

import requests
import json
import os
import mimetypes
import Image
import cStringIO
import base64

def reddit_login(username, password):
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

def imgur_login(app_id):
    auth_header = 'Client-ID ' + app_id
    headers = {'Authorization': auth_header}
    client = requests.session()
    client.headers = headers

    return client

def new_stories(client, subreddit):
    params = {'limit': 100,}
    url = "http://www.reddit.com/r/{sr}/new.json".format(sr=subreddit)
    req = client.get(url, params=params)
    res = json.loads(req.text)
    return res['data']['children']

def load_image(url):
    req = requests.get(url)
    sio = cStringIO.StringIO(req.content)
    img = Image.open(sio)
    return img

def gif_frames(img):
    frames = []
    palette = img.getpalette()

    try:
        while True:
            img.putpalette(palette)
            new_img = Image.new("RGBA", img.size)
            new_img.paste(img)
            frames.append(new_img)

            img.seek(img.tell()+1)
    except EOFError:
        pass
    return frames

def base64_encode_image(img):
    sio = cStringIO.StringIO()
    img.save(sio, 'PNG')
    res = base64.b64encode(sio.getvalue())
    return res

client = reddit_login('GifExploderBot', os.environ['GIFEXPLODERBOT_PASSWORD'])
imgur_client = imgur_login('9faa2c6310ad5ba')
stories = new_stories(client, 'MapPorn')

for story in stories:
    mimetype = mimetypes.guess_type(story['data']['url'])[0]
    if mimetype == "image/gif":
        frames = gif_frames(load_image(story['data']['url']))
        if len(frames) > 1:
            print "{n}: {u} {l}".format(n=story['data']['title'].encode('utf-8'), u=story['data']['url'], l=len(frames))
            for frame in frames:
                print len(base64_encode_image(frame))
            break
