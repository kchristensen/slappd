#!/usr/bin/env python3.5
"""
The MIT License

Copyright (c) 2015 Kyle Christensen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from configparser import SafeConfigParser
from operator import itemgetter
import json
import os
import re
import requests
import sys


def config_load():
    """Instantiates a global configparser object from the config file"""
    global cfg

    cfg_file = config_path()
    if not os.path.exists(cfg_file):
        raise OSError(2, 'Configuration file does not exist', cfg_file)
    else:
        cfg = SafeConfigParser()
        cfg.read(cfg_file)


def config_path():
    return os.path.dirname(os.path.realpath(__file__)) + '/slappd.cfg'


def config_update():
    """Updates the config file with any changes that have been made"""
    cfg_file = config_path()

    try:
        with open(cfg_file, 'w') as fd:
            cfg.write(fd)
    except EnvironmentError:
        print('There was an error writing to the config file')
        sys.exit(1)


def fetch_untappd_activity():
    """Returns a requests object full of Untappd API data"""
    try:
        r = requests.get(fetch_url('checkin/recent'), timeout=2)
        r.encoding = 'utf-8'
        return r.text
    except ConnectionError:
        print('There was an error connecting to the Untappd API')
        sys.exit(1)


def fetch_url(method):
    """Returns an API url with credentials inserted"""
    return "https://api.untappd.com/v4/{}?" \
        "client_id={}&client_secret={}&access_token={}&min_id={}".format(
            method,
            cfg.get('untappd', 'id'),
            cfg.get('untappd', 'secret'),
            cfg.get('untappd', 'token'),
            cfg.get('untappd', 'lastseen'))


def slack_message(token, text, icon, title=None, thumb=None):
    """Sends a Slack message via webhooks"""
    url = 'https://hooks.slack.com/services/' + token
    # If thumb is set, we're sending a badge notification
    if thumb is not None:
        # Strip any HTML in text returned from Untappd
        payload = {
            'attachments': [
                {
                    'title': title,
                    'text': strip_html(text),
                    'thumb_url': thumb
                }
            ],
            'icon_url': icon,
            'username': 'Untappd'
        }
    else:
        payload = {
            'icon_url': icon,
            'text': text,
            'username': 'Untappd'
        }
    try:
        requests.post(url, json=payload)
    except ConnectionError:
        print('There was an error connecting to the Slack API')
        sys.exit(1)


def strip_html(text):
    return re.sub(r'<[^>]*?>', '', text)


def main():
    """Where the magic happens"""
    config_load()
    data = json.loads(fetch_untappd_activity())

    if data['meta']['code'] == 200:
        checkins = data['response']['checkins']['items']
        slack_token = cfg.get('slack', 'token')
        text = ''
        for checkin in checkins:
            user = checkin['user']['user_name'].lower()
            # If this is one of our watched users, let's send a Slack message
            if user in cfg.get('untappd', 'users'):
                # If any users earned badges, let's send individual messages
                for badge in checkin['badges']['items']:
                    title = "{} {} earned the {} badge!" \
                        .format(
                            checkin['user']['first_name'],
                            checkin['user']['last_name'],
                            badge['badge_name'])
                    slack_message(
                        slack_token,
                        badge['badge_description'],
                        badge['badge_image']['sm'],
                        title,
                        badge['badge_image']['md'])

                # Lump all of the check-ins together as one message
                text += ":beer: *<{0}/user/{1}|{2} {3}>* is " \
                    "drinking a *<{0}/b/{8}/{4}|{5}>* by " \
                    "*<{0}/w/{8}/{7}|{6}>*".format(
                        'https://untappd.com',
                        checkin['user']['user_name'],
                        checkin['user']['first_name'],
                        checkin['user']['last_name'],
                        checkin['beer']['bid'],
                        checkin['beer']['beer_name'],
                        checkin['brewery']['brewery_name'],
                        checkin['brewery']['brewery_id'],
                        checkin['brewery']['brewery_slug'])

                # If there's a location, include it
                if checkin['venue']:
                    text += " at *<{}/v/{}/{}|{}>*".format(
                        'https://untappd.com',
                        checkin['venue']['venue_slug'],
                        checkin['venue']['venue_id'],
                        checkin['venue']['venue_name'])

                # If there's a rating, include it
                if int(checkin['rating_score']):
                    text += " ({}/5)\n".format(checkin['rating_score'])
                else:
                    text += "\n"

                # If there's a check-in comment, include it
                if len(checkin['checkin_comment']):
                    text += ">\"{}\"\n".format(checkin['checkin_comment'])

        # Send a message if there has been any check-in activity
        if len(text):
            slack_message(
                slack_token,
                text,
                checkin['beer']['beer_label'])

        # Find the id of the most recent check-in
        if data['response']['checkins']['count']:
            cfg.set(
                'untappd',
                'lastseen',
                str(max(data['response']['checkins']['items'],
                    key=itemgetter('checkin_id'))['checkin_id']))

            # Update the config file with the last check-in seen
            config_update()

    else:
        print("Untappd API returned http code {}".format(data['meta']['code']))
        sys.exit(1)


if sys.version_info >= (3, 5):
    if __name__ == '__main__':
        main()
else:
    print('This script requires Python 3.5 or greater.')
    sys.exit(1)
