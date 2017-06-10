#!/usr/bin/env python3
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
import os
import re
import sys
import requests


def config_load():
    """ Instantiates a global configparser object from the config file """
    # pylint: disable=I0011,C0103,W0601
    global cfg

    cfg_file = config_path()
    if not os.path.exists(cfg_file):
        sys.exit('Error: Configuration file {} does not exist'
                 .format(cfg_file))
    else:
        cfg = SafeConfigParser()
        cfg.read(cfg_file)


def config_path():
    """ Return the patch to the slappd configuration file """
    return os.path.dirname(os.path.realpath(__file__)) + '/slappd.cfg'


def config_update():
    """ Updates the config file with any changes that have been made """
    cfg_file = config_path()

    try:
        with open(cfg_file, 'w') as cfg_handle:
            cfg.write(cfg_handle)
    except EnvironmentError:
        sys.exit('Error: Writing to the configuration file {}'
                 .format(cfg_file))


def fetch_untappd_activity():
    """ Returns a requests object full of Untappd API data """
    timeout = cfg.getint('untappd', 'timeout', fallback=10)
    try:
        request = requests.get(fetch_url('checkin/recent'), timeout=timeout)
        request.encoding = 'utf-8'
        return request.json()
    except requests.exceptions.Timeout:
        sys.exit('Error: Untappd API timed out after {} seconds'
                 .format(timeout))
    except requests.exceptions.RequestException:
        sys.exit('Error: There was an error connecting to the Untappd API')


def fetch_url(method):
    """ Returns an API url with credentials inserted """
    return 'https://api.untappd.com/v4/{}?' \
        'client_id={}&client_secret={}&access_token={}&min_id={}'.format(
            method,
            cfg.get('untappd', 'id'),
            cfg.get('untappd', 'secret'),
            cfg.get('untappd', 'token'),
            cfg.get('untappd', 'lastseen'))


def slack_message(images=None, msg_type=None, text=None):
    """ Sends a Slack message via webhooks """
    url = 'https://hooks.slack.com/services/' + cfg.get('slack', 'token')
    if msg_type == 'badge':
        payload = {
            'attachments': [
                {
                    'text': strip_html(text),
                    'thumb_url': images['thumb_url'],
                    'title': images['title']
                }
            ],
            'icon_url': images['icon_url'],
            'username': 'Untappd'
        }
    elif msg_type == 'photo':
        payload = {
            'attachments': [
                {
                    'image_url': images['image_url'],
                    'title': images['title']
                }
            ],
            'icon_url': images['icon_url'],
            'text': text,
            'username': 'Untappd'
        }
    else:
        payload = {
            'icon_url': images['icon_url'],
            'text': text,
            'username': 'Untappd'
        }

    try:
        requests.post(url, json=payload)
    except requests.exceptions.RequestException:
        sys.exit('Error: There was an error connecting to the Slack API')


def strip_html(text):
    """ Strip html tags from text """
    return re.sub(r'<[^>]*?>', '', text)


def main():
    """ Where the magic happens """
    config_load()
    data = fetch_untappd_activity()

    if data['meta']['code'] == 200:
        checkins = data['response']['checkins']['items']
        defer_sending = True
        images = {}
        text = ''

        # If any of our user's check-ins contain a photo
        # send messages immediately so pictures are immediately
        # after the check-in.
        for checkin in reversed(checkins):
            user = checkin['user']['user_name'].lower()
            if user in cfg.get('untappd', 'users') \
                    and int(checkin['media']['count']):
                defer_sending = False

        for checkin in reversed(checkins):
            user = checkin['user']['user_name'].lower()
            # If this is one of our watched users, let's send a Slack message
            if user in cfg.get('untappd', 'users'):
                # If any users earned badges, let's send individual messages
                for badge in checkin['badges']['items']:
                    title = '{} {} earned the {} badge!' \
                        .format(
                            checkin['user']['first_name'],
                            checkin['user']['last_name'],
                            badge['badge_name'])
                    images['icon_url'] = badge['badge_image']['sm']
                    images['thumb_url'] = badge['badge_image']['md']
                    images['title'] = title
                    slack_message(
                        images=images,
                        msg_type='badge',
                        text=badge['badge_description'])

                text += ':beer: *<{0}/user/{1}|{2} {3}>* is ' \
                    'drinking a *<{0}/b/{8}/{4}|{5}>* by ' \
                    '*<{0}/w/{8}/{7}|{6}>*'.format(
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
                    text += ' at *<{}/v/{}/{}|{}>*'.format(
                        'https://untappd.com',
                        checkin['venue']['venue_slug'],
                        checkin['venue']['venue_id'],
                        checkin['venue']['venue_name'])

                # If there's a rating, include it
                if int(checkin['rating_score']):
                    text += " ({}/5)".format(checkin['rating_score'])
                text += "\n"

                # If there's a check-in comment, include it
                if len(checkin['checkin_comment']):
                    text += ">\"{}\"\n".format(checkin['checkin_comment'])

                # Use the beer label as an icon if it exists
                if len(checkin['beer']['beer_label']):
                    images['icon_url'] = checkin['beer']['beer_label']

                # If there's a photo, optionally include it in the message
                if int(checkin['media']['count']) \
                        and cfg.getboolean('untappd', 'display_media'):
                    media = checkin['media']['items'].pop()
                    images['image_url'] = media['photo']['photo_img_md']
                    images['title'] = checkin['beer']['beer_name']
                    slack_message(
                        images=images,
                        msg_type='photo',
                        text=text)
                # We're sending regular check-ins one at a time this execution
                elif not defer_sending:
                    slack_message(
                        images=images,
                        text=text)

                # If we're not deferring messages, stop concatenating
                # text to avoid duplicate check-ins
                if not defer_sending:
                    text = ''

        if len(text) and defer_sending:
            slack_message(
                images=images,
                text=text)

        # Find the id of the most recent check-in
        if data['response']['checkins']['count']:
            cfg.set(
                'untappd',
                'lastseen',
                str(max(data['response']['checkins']['items'],
                        key=itemgetter('checkin_id'))['checkin_id']))

            # Update the config file with the last check-in seen
            config_update()
    elif data['meta']['error_type'] == 'invalid_limit':
        sys.exit('Error: Untappd API rate limit reached, try again later')
    else:
        sys.exit('Error: Untappd API returned http code {}'
                 .format(data['meta']['code']))


if sys.version_info >= (3, 5):
    if __name__ == '__main__':
        main()
else:
    sys.exit('Error: This script requires Python 3.5 or greater.')
