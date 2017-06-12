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
from jinja2 import Environment, FileSystemLoader
import requests

# Global ConfigParser object for configuration options
CONFIG = SafeConfigParser()


def check_for_photos(checkins):
    """ Check if any checks-in contain photos """
    for checkin in checkins:
        user = checkin['user']['user_name'].lower()
        if user in CONFIG.get('untappd', 'users') \
                and int(checkin['media']['count']):
            return False

    return True


def config_load():
    """ Load configuration options from file """
    config_file = get_cwd() + '/slappd.cfg'
    if not os.path.exists(config_file):
        sys.exit('Error: Configuration file {} does not exist'
                 .format(config_file))
    else:
        CONFIG.read(config_file)


def config_update():
    """ Updates the config file with any changes that have been made """
    config_file = get_cwd() + '/slappd.CONFIG'
    try:
        with open(config_file, 'w') as cfg_handle:
            CONFIG.write(cfg_handle)
    except EnvironmentError:
        sys.exit('Error: Could not write to configuration file {}'
                 .format(config_file))


def fetch_untappd_activity():
    """ Returns a requests object full of Untappd API data """
    timeout = CONFIG.getint('untappd', 'timeout', fallback=10)
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
            CONFIG.get('untappd', 'id'),
            CONFIG.get('untappd', 'secret'),
            CONFIG.get('untappd', 'token'),
            CONFIG.get('untappd', 'lastseen'))


def get_cwd():
    """ Return the current working directory """
    return os.path.dirname(os.path.realpath(__file__))


def slack_message(images=None, msg_type=None, text=None):
    """ Sends a Slack message via webhooks """
    url = 'https://hooks.slack.com/services/' + CONFIG.get('slack', 'token')
    payload = {
        'icon_url': images['icon_url'],
        'username': 'Untappd',
        'text': text
    }
    if msg_type == 'badge':
        payload['attachments'] = [{
            'text': strip_html(text),
            'thumb_url': images['thumb_url'],
            'title': images['title']
        }]
        payload['text'] = None
    elif msg_type == 'photo':
        payload['attachments'] = [{
            'image_url': images['image_url'],
            'title': images['title']
        }]

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
    env = Environment(loader=FileSystemLoader(get_cwd() + '/templates'))

    if data['meta']['code'] == 200:
        checkins = data['response']['checkins']['items']
        images = {}
        text = ''
        tmpl = env.get_template('check-in.j2')

        # If any check-ins contain photos, send each message individually
        # so pictures appear immediately after the check-in.
        defer_sending = check_for_photos(checkins)

        for checkin in reversed(checkins):
            user = checkin['user']['user_name'].lower()
            # If this is one of our watched users, let's send a Slack message
            if user in CONFIG.get('untappd', 'users'):
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

                # Render the message from a Jinja2 template
                text += tmpl.render(checkin=checkin,
                                    untappd_domain='https://untappd.com')

                # Use the beer label as an icon if it exists
                if len(checkin['beer']['beer_label']):
                    images['icon_url'] = checkin['beer']['beer_label']

                # If there's a photo, optionally include it in a second message
                if int(checkin['media']['count']) \
                        and CONFIG.getboolean('untappd', 'display_media'):
                    media = checkin['media']['items'].pop()
                    images['image_url'] = media['photo']['photo_img_md']
                    images['title'] = checkin['beer']['beer_name']
                    slack_message(
                        images=images,
                        msg_type='photo',
                        text=text)
                    text = ''
                # We're sending regular check-ins one at a time this execution
                elif not defer_sending:
                    slack_message(
                        images=images,
                        text=text)
                    text = ''

        # We're not deferring, so lump all the messages together
        if len(text) and defer_sending:
            slack_message(
                images=images,
                text=text)

        # Find the id of the most recent check-in
        if data['response']['checkins']['count']:
            CONFIG.set(
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
    sys.exit('Error: This script requires Python 3.5 or greater')
