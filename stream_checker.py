import requests
import json
import pymysql
from time import gmtime, strftime
import botconfig as cfg

# Slack related
slack = cfg.slack['slack']

# Database config & connection
cnx = pymysql.connect(user=cfg.mysql['user'], passwd=cfg.mysql['passwd'], host=cfg.mysql['host'], db=cfg.mysql['db'])
cursor = cnx.cursor()


def twitch():
    """ Script to check given Twitch usernames online status and post stream info to Slack if online """
    
    print('Twitch bot started')
    query = 'SELECT usernames FROM twitch'
    cursor.execute(query)
    streams = cursor.fetchall()

    online_status = {}

    # Url list generated from base url
    urls = []

    # Notify user when the list started over
    print('Running the list')

    # Generate API urls
    for user_name in streams:
        link = cfg.twitch['api']+user_name[0]
        urls.append(link)

    # Check if stream is up or down, if stream is up post is to slack
    for full_url in urls:
        r = requests.get(full_url, headers=cfg.twitch_payload)
        data = json.loads(r.text)

        # Stream down, post url and stream down
        try:
            if data[u'stream'] is None:
                print('{} - {} is currently offline'.format(strftime("%H:%M:%S", gmtime()), full_url[37:]))
                try:
                    offline = 'UPDATE twitch SET online = 0 WHERE usernames = {}'.format(full_url[37:])
                    cursor.exceute(offline)
                    cnx.commit()
                except NoneType as fail:
                    print(fail)
                    pass
            else:
                online_check = 'SELECT online, usernames FROM twitch'
                cursor.execute(online_check)
                status = cursor.fetchall()
                for username, online in status:
                    online_status[online] = username
                if online_status[data[u'stream'][u'channel'][u'name'].lower()] == 1:
                    print('{} is marked online - passing...'.format(data[u'stream'][u'channel'][u'name']))
                    pass
                else:
                    requests.post(slack, json.dumps({
                        'username': cfg.twitch['name'], 'icon_emoji': cfg.twitch['icon'], 'channel': '#main-chat',
                        'attachments': [{'fallback': '{} is live playing {} on <{}|Twitch.tv>'.format(
                            data[u'stream'][u'channel'][u'name'],
                            data[u'stream'][u'game'],
                            data[u'stream'][u'channel'][u'url']),
                            'title': '{} is live playing {}'.format(data[u'stream'][u'channel'][u'name'],
                                                                    data[u'stream'][u'game']),
                            'title_link': data[u'stream'][u'channel'][u'url'],
                            'image_url': data[u'stream'][u'preview'][u'medium'], 'color': '#7CD197'}]
                    }
                    )
                                  )
                    print('{} posted to main chat in Slack'.format(data[u'stream'][u'channel'][u'name']))
                    # Set select username's online status to True
                    online = 'UPDATE twitch SET online = 1 WHERE usernames = {}'.format(
                        data[u'stream'][u'channel'][u'name'])
                    cursor.exceute(online)
                    cnx.commit()
        except KeyError:
            pass
    print('Bot done')


def mixer():
    """ Script to check given Mixer usernames online status and post stream info to Slack if online"""
    print('Mixer bot started')
    query = 'SELECT usernames FROM mixer'
    cursor.execute(query)
    streams = cursor.fetchall()

    urls = []
    online_status = {}

    for user_name in streams:
        link = cfg.mixer['api'].format(user_name[0])
        urls.append(link)

    # Check if stream is up or down, if stream is up post is to slack
    for full_url in urls:
        r = requests.get(full_url)
        data = json.loads(r.text)
        # Stream down, post url and stream down
        try:
            if data['online'] is False:
                print('{} - {} is currently offline'.format(strftime("%H:%M:%S", gmtime()),
                                                            full_url[34:-8]))
                offline = 'UPDATE mixer SET online = 0 WHERE usernames = "{}"'.format(
                    data['token'])
                cursor.execute(offline)
                cnx.commit()
            else:
                online_check = 'SELECT online, usernames FROM mixer'
                cursor.execute(online_check)
                status = cursor.fetchall()
                for username, online in status:
                        online_status[online] = username
                if online_status[data['token'].lower()] == 1:
                    print('{} is marked online - passing...'.format(data['token']))
                    pass
                else:
                    requests.post(slack, json.dumps(
                        {'username': cfg.mixer['name'], 'icon_emoji': cfg.mixer['icon'],
                            'channel': '#ignorethis', 'attachments': [{
                                'fallback': '{} is live playing {} on <https://mixer.com/{}|Mixer>'.format(
                                    data['token'], data['type']['name'], data['token']),
                                'title': '{} is live playing {}'.format(data['token'], data['type']['name']),
                                'title_link': 'https://mixer.com/{}'.format(data['token']),
                                'image_url': 'https://thumbs.mixer.com/channel/{}.small.jpg'.format(data['id']),
                                'color': '#7CD197'}]}))

                    print('{} posted to main chat in Slack'.format(data['token']))

                    # Set select username's online status to True
                    online = 'UPDATE mixer SET online = 1 WHERE usernames = "{}"'.format(data['token'])
                    cursor.execute(online)
                    cnx.commit()
        except KeyError:
            pass

    print('Bot done')


twitch()
mixer()
