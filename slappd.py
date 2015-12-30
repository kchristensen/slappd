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
import requests


def getURL(cfg, method):
    """Returns an API url with credentials inserted"""
    return "https://api.untappd.com/v4/{}?" \
        "client_id={}&client_secret={}&access_token={}&min_id={}".format(
            method,
            cfg.get('untappd', 'id'),
            cfg.get('untappd', 'secret'),
            cfg.get('untappd', 'token'),
            cfg.get('untappd', 'lastseen'))


def loadConfig(cfg_file):
    """Returns a configparser object from the parsed config file"""
    if not os.path.exists(cfg_file):
        raise OSError('ERROR: Configuration file slappd.cfg does not exist')
    cfg = SafeConfigParser()
    cfg.read(cfg_file)
    return cfg


def notifySlack(msg, thumb, token):
    """Sends a Slack message via webhooks"""
    url = 'https://hooks.slack.com/services/' + token
    payload = {
        'icon_url': thumb,
        'text': msg,
        'username': 'Untappd'
    }
    try:
        requests.post(url, data=json.dumps(payload))
    except ConnectionError:
        print('There was an error connecting to the Slack API')


def getUntappdActivity(cfg):
    """Returns a requests object full of Untappd API data"""
    try:
        return requests.get(getURL(cfg, 'checkin/recent')).text
    except ConnectionError:
        print('There was an error connecting to the Untappd API')


def main():
    """Where the magic happens"""
    cfg_file = os.path.dirname(os.path.realpath(__file__)) + '/slappd.cfg'
    cfg = loadConfig(cfg_file)
    data = json.loads(getUntappdActivity(cfg))
    msg = ''

    if data['meta']['code'] == 200:
        for checkin in data['response']['checkins']['items']:
            user = checkin['user']['user_name'].lower()
            # If this is one of our watched users, let's send a Slack message
            if user in cfg.get('untappd', 'users'):
                msg += ":beer: *<{0}/user/{1}|{2} {3}>* is " \
                    "drinking a *<{0}/b/{8}/{4}|{5}>* by " \
                    "*<{0}/w/{8}/{7}|{6}>* ({9}/5)\n".format(
                     'http://untappd.com',
                     checkin['user']['user_name'],
                     checkin['user']['first_name'],
                     checkin['user']['last_name'],
                     checkin['beer']['bid'],
                     checkin['beer']['beer_name'],
                     checkin['brewery']['brewery_name'],
                     checkin['brewery']['brewery_id'],
                     checkin['brewery']['brewery_slug'],
                     checkin['rating_score'])

                # If there's a check-in comment, include it
                if len(checkin['checkin_comment']):
                    msg += "\n>\"{0}\"\n".format(checkin['checkin_comment'])

        # Send a message if there has been any activity
        if len(msg):
            notifySlack(
                msg,
                checkin['beer']['beer_label'],
                cfg.get('slack', 'token'))

        # Find the id of the most recent checkin
        if data['response']['checkins']['count']:
            cfg.set(
                'untappd',
                'lastseen',
                str(max(data['response']['checkins']['items'],
                    key=itemgetter('checkin_id'))['checkin_id']))

            # Update the config file with the last checkin seen
            try:
                with open(cfg_file, 'w') as fd:
                    cfg.write(fd)
            except EnvironmentError:
                print('There was an error writing to the config file')


if __name__ == '__main__':
    main()
