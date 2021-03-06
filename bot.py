# -*- coding: utf-8 -*-

import requests
import json
import os
import mimetypes
import Image
import cStringIO
import base64
import sqlite3

def connect_to_db():
    if os.path.exists("gifexploderbot.db"):
        return sqlite3.connect("gifexploderbot.db")
    else:
        return create_db()

def create_db():
    print "Creating db"
    conn = sqlite3.connect("gifexploderbot.db")
    f = open('schema.sql')
    conn.executescript(f.read())
    f.close()
    conn.commit()
    return conn

DB = connect_to_db()

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
    
    db_res = DB.execute("SELECT last_fetched FROM subreddits WHERE name=?", (subreddit, )).fetchall()
    if db_res != []:
        params['before'] = db_res[0][0]

    url = "http://www.reddit.com/r/{sr}/new.json".format(sr=subreddit)
    req = client.get(url, params=params)
    res = json.loads(req.text)

    print 
    last_fetched = res['data']['children'][0]['data']['name']

    if db_res == []:
        DB.execute("INSERT INTO subreddits (name, last_fetched) VALUES (?,?)", (subreddit, last_fetched))
        DB.commit()
    else:
        DB.execute("UPDATE subreddits SET last_fetched=? WHERE name=?", (last_fetched, subreddit))
        DB.commit()

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

def create_album(client, imgs):
    req = client.post("https://api.imgur.com/3/album/")
    res = json.loads(req.content)
    album_id = res['data']['id']
    album_dh = res['data']['deletehash']

    for img in imgs:
        post_data = {"image": base64_encode_image(img), "album": album_dh}
        req = client.post("https://api.imgur.com/3/image", data=post_data)

    return res

def post_comment(client, parent, url):
    comment_template = "Here is a link to an album containing the frames of the animated gif: [{url}]({url})"
    comment = comment_template.format(url="http://www.imgur.com/a/"+url)

    params = {"api_type":"json", "text": comment, "thing_id": parent}
    client.post("http://www.reddit.com/api/comment", data=params)

client = reddit_login('GifExploderBot', os.environ['GIFEXPLODERBOT_PASSWORD'])
imgur_client = imgur_login('9faa2c6310ad5ba')

stories = new_stories(client, 'MapPorn')

for story in stories:
    mimetype = mimetypes.guess_type(story['data']['url'])[0]
    if mimetype == "image/gif":
        print "Fetching image for " + story['data']['name']
        frames = gif_frames(load_image(story['data']['url']))
        if len(frames) > 1:
            print "Creating album for " + story['data']['name']
            album_info = create_album(imgur_client, frames)
            DB.execute("INSERT INTO threads (id, album_id, deletehash) VALUES (?,?,?)", (story['data']['name'], album_info['data']['id'], album_info['data']['deletehash']))
            DB.commit()
            print "Posting comment for " + story['data']['name']
            post_comment(client, story['data']['name'], album_info['data']['id'])
            # break
            # print story['data']
            # print "{i} {n}: {u} {l}".format(i=story['data']['id'],n=story['data']['title'].encode('utf-8'), u=story['data']['url'], l=len(frames))