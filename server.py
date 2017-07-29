import requests
import json
from bs4 import BeautifulSoup
import pymysql
import cherrypy
import os
import botconfig as cfg

# Posted urls
online = []

# MySQL database credentials
cnx = pymysql.connect(user=cfg.mysql['user'], passwd=cfg.mysql['passwd'], host=cfg.mysql['host'], db=cfg.mysql['db'])
cursor = cnx.cursor()


class Server(object):

    exposed = True

    def GET(*args, **kwargs):

        html = """<html><head><title>CherryPy server</title>\
        </head><body><h1>What are you doing here?</h1><p>The server is working just 
        fine</p></body></html>"""

        return html.encode('utf-8')

    def POST(*args, **kwargs):
        # Response to HTTP POST from Slack to add and remove users from the streamer list
        # If user is already on the list the bot responses back with "username already on the list"
        json_parse = json.dumps(cherrypy.request.body.params)
        decoded = json.loads(json_parse)
        trigger = decoded['text']

        if '!xbl' in trigger:
                
            r = requests.get('http://support.xbox.com/en-US/xbox-live-status?icid=furl_status')
            soup = BeautifulSoup(r.content, 'html5lib')
            g_data = soup.find_all("ul", {"class": "core"})
            status = {}

            for item in g_data:
                for service in item.findAll('h3', {'class': 'servicename'}):
                    status[service.text] = []
                for service, platform in zip(item.findAll('h3', {'class': 'servicename'}),
                                             item.findAll('div', {'class': 'platforms'})):
                    for platform in platform.findAll('div', {'class': 'label'}):
                        status[service.text].append(platform.text)

            output_ok = []
            output_down = []

            for service, platform in status.items():
                if platform:
                    plat_string = ', '.join(platform)
                    output_down.append('{} is limited. Platforms: {}\n'.format(service, plat_string))
                else:
                    output_ok.append('{} is up and running.\n'.format(service))
                str_ok = ''.join(output_ok)
                str_down = ''.join(output_down)

            if output_ok and output_down:
                return json.dumps({'username': cfg.xbl['name'], 'icon_emoji': cfg.xbl['icon'],
                                   'attachments': [{'fallback': str_ok, 'title': 'These systems are online:',
                                                    'text': str_ok, 'color': '#008000'},
                                                   {'fallback': str_down, 'title': 'These systems are down:',
                                                    'text': str_down, 'color': '#FF0000'
                                                    }]
                                   }).encode('utf-8')

            elif output_down:
                return json.dumps({'username': cfg.xbl['name'], 'icon_emoji': cfg.xbl['icon'],
                                   'attachments': [{'fallback': str_down, 'title': 'These systems are down:',
                                                    'text': str_down, 'color': '#FF0000'
                                                    }]
                                   }).encode('utf-8')

            else:
                return json.dumps({'username': cfg.xbl['name'], 'icon_emoji': cfg.xbl['icon'],
                                   'attachments': [{'fallback': str_ok, 'title': 'These systems are online:',
                                                    'text': str_ok, 'color': '#008000'
                                                    }]
                                   }).encode('utf-8')

        elif '!mixer' in trigger:
            keyword = trigger[7:10]
            if keyword == 'add':
                user = trigger[11:]
                if user in user_check_mixer(user):
                    print(user + ' is already on the list.')
                    return json.dumps({'username': '{}'.format(cfg.mixer['name']),
                                       'icon_emoji': '{}'.format(cfg.mixer['icon']),
                                       'text': user + ' is already on the list.'
                                       }).encode('utf-8')
                else:
                    add = 'INSERT INTO mixer(usernames) VALUES ("{}")'.format(user.lower().strip())
                    cursor.execute(add)
                    cnx.commit()
                    print(user + ' added to streamer database.')
                    return json.dumps({'usename': '{}'.format(cfg.mixer['name']),
                                       'icon_emoji': '{}'.format(cfg.mixer['icon']),
                                       'text': user + ' added to streamer database.'
                                       }).encode('utf-8')

            elif keyword == 'rem':         
                user = trigger[11:]
                if user not in user_check_mixer(user):
                    print(user + ' is not on the list.')
                    return json.dumps({'username': '{}'.format(cfg.mixer['name']),
                                       'icon_emoji': '{}'.format(cfg.mixer['icon']),
                                       'text': user + ' is not on the list.'
                                       }).encode('utf-8')
                else:
                    remove = 'DELETE FROM mixer WHERE usernames = "{}"'.format(user.lower().strip())
                    cursor.execute(remove)
                    cnx.commit()
                    print(user + ' removed from streamer database.')
                    return json.dumps({'username': '{}'.format(cfg.mixer['name']),
                                       'icon_emoji': '{}'.format(cfg.mixer['icon']),
                                       'text': user + ' removed from streamer database.'
                                       }).encode('utf-8')

            elif keyword == 'lst':

                print('Userlist was asked. ' + ', '.join(user_check_mixer()))
                return json.dumps({
                    'username': '{}'.format(cfg.mixer['name']), 'icon_emoji': '{}'.format(cfg.mixer['icon']),
                    'text': 'Currently these users are on my list:\n' + ', '.join(user_check_mixer())
                            + '\nIf you are not on my list, use "!mixer add _username_" or if you want to remove yourself from the list use "!mixer rem _username_"'
                }).encode('utf-8')
            else:
                print(trigger + ' (Wrong keyword used)')
                return json.dumps({
                    'username': '{}'.format(cfg.mixer['name']), 'icon_emoji': '{}'.format(cfg.mixer['icon']),
                    'text': 'Please check your keyword. I understand only "add", "rem" or "lst".\nSo a working command is "!mixer add/rem _username_ where the username is the one in the actual Mixer.com url or "!mixer lst" which lists all added users'
                }).encode('utf-8')
                
        elif '!twitch' in trigger:
            keyword = trigger[8:11]
            if keyword == 'add':
                user = trigger[12:]
                if user in user_check_twitch(user):
                    print(user + ' is already on the list.')
                    return json.dumps({'user': '{}'.format(cfg.twitch['name']),
                                       'icon_emoji': '{}'.format(cfg.twitch['icon']),
                                       'text': user + ' is already on the list.'
                                       }).encode('utf-8')
                else:
                    add = 'INSERT INTO twitch(usernames) VALUES ("{}")'.format(user.lower().strip())
                    cursor.execute(add)
                    cnx.commit()
                    print(user + ' added to streamer database.')
                    return json.dumps({'user': '{}'.format(cfg.twitch['name']),
                                       'icon_emoji': '{}'.format(cfg.twitch['icon']),
                                       'text': user + ' added to streamer database.'
                                       }).encode('utf-8')

            elif keyword == 'rem':
                user = trigger[12:]
                if user not in user_check_twitch(user):
                    print(user + ' is not on the list.')
                    return json.dumps({'user': '{}'.format(cfg.twitch['name']),
                                       'icon_emoji': '{}'.format(cfg.twitch['icon']),
                                       'text': user + ' is not on the list.'
                                       }).encode('utf-8')
                else:
                    remove = 'DELETE FROM twitch WHERE usernames = "{}"'.format(user.lower().strip())
                    cursor.execute(remove)
                    cnx.commit()
                    print(user + ' removed from streamer database.')
                    return json.dumps({'user': '{}'.format(cfg.twitch['name']),
                                       'icon_emoji': '{}'.format(cfg.twitch['icon']),
                                       'text': user + ' removed from streamer database.'
                                       }).encode('utf-8')

            elif keyword == 'lst':
                print('Userlist was asked. ' + ', '.join(user_check_twitch()))
                return json.dumps({
                    'user': '{}'.format(cfg.twitch['name']), 'icon_emoji': '{}'.format(cfg.twitch['icon']),
                    'text': 'Currently these users are on my list:\n'
                            + ', '.join(user_check_twitch()) + '\nIf you are not on my list, use "!twitch add _username_" or if you want to remove yourself from the list use "!twitch rem  _username_"'
                }).encode('utf-8')
        
        else:
            return json.dumps({
                'text': "I did not understand your keyword. It\'s _!twitch_, _!mixer_ or _!xbl_"
            }).encode('utf-8')


def user_check_twitch(*args, **kwargs):
    # This is for checking whether the given username is already added to the list
    user = []
    query = 'SELECT usernames FROM twitch'
    cursor.execute(query)
    users = cursor.fetchall()

    for username in users:
        users = list(username)
        user.append(users[0])

    return user


def user_check_mixer(*args, **kwargs):

    # This is for checking whether the given username is already added to the list
    user = []
    query = 'SELECT usernames FROM mixer'
    cursor.execute(query)
    users = cursor.fetchall()

    for username in users:
        users = list(username)
        user.append(users[0])

    return user


def config():  # CherryPy server conf files
    os.chdir(cfg.config['dir'])
    cherrypy.quickstart(Server(), '//', 'app.conf')

        
if __name__ == '__main__':
    print("Bot started!")
    config()
