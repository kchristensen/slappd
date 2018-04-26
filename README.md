# slappd

### About

Since Untappd does not currently support callbacks or webhooks, I wrote a basic
Slack integration that will relay check-ins and badges earned for specified users
on your feed to a Slack channel.

![Screenshot](screenshot.png)

This script is designed to be run from crontab, and issues one API call per run.

### Known Issues

* The first time you run the script, it may be a little chatty because it has
  not previously seen your feed before.
* If you have a lot of Untappd friends, but are only watching a subset of them,
  you may miss check-ins if you don't run Slappd regularly.

### Requirements

* Python 3.5+ (It may run on >= 3.0, but I have not tested.)
* Some Python modules (configparser, Jinja2, simplejson, requests)
* A way of periodically running this script (at, cron, etc)
* Untappd [API access](https://untappd.com/api/register?register=new)
* A Slack channel full of beer lovers

### Installation & Configuration

If this is your first time, create the default config file with `make config`
and then edit it (`~/.config/slappd/slappd.cfg`) to reflect your API information
and friends list.

#### Docker

* Run `make docker-run` to build and run Slappd. **Note:** This mounts the
  config you created earlier into the container to keep track of which check-ins
  it has seen.

#### Virtualenv

* Install Slappd to a virtualenv via `make install`.
* Run it from crontab: `*/5 * * * ~/.virtualenv/slappd/bin/slappd > /dev/null 2>&1`