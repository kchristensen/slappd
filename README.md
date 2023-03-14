# Slappd - An Slack integration for Untappd

## About

Since Untappd does not currently support callbacks or webhooks, I wrote a basic Slack integration that will relay check-ins and badges earned for specified users on your feed to a Slack channel.

![Screenshot](https://github.com/kchristensen/slappd/blob/master/screenshot.png?raw=true)

This script is designed to be run from crontab, and issues one API call per run.

## Known Issues

* The first time you run the script, it may be a little chatty because it has not previously seen your feed before.
* If you have a lot of Untappd friends, but are only watching a subset of them, you may miss check-ins if you don't run Slappd regularly.

## Requirements

* Docker, or the ability to create a [Virtual Environment](https://docs.python.org/3/tutorial/venv.html)
* Python 3.6+ and a couple of common Python modules: (configparser, Jinja2, requests)
* A way of periodically running this script (at, cron, etc)
* Untappd [API access](https://untappd.com/api/register?register=new)
* A Slack channel full of beer lovers

## Configuration

The first time you run Slappd, it will attempt to create a config file (`~/.config/slappd/slappd.cfg`). You should edit it to reflect your Untappd API information and friends list.

## Running Slappd

### GitHub Container Registry

Slappd is available on the [GitHub Container Registry](https://github.com/features/packages), so you don't have to build it if you don't want to. You can simply add this to your crontab, and after you've edited the config, you're off.

`*/5 * * * * docker run --name slappd --rm -v ${HOME}/.config/slappd:/home/slappd/.config/slappd ghcr.io/kchristensen/slappd > /dev/null 2>&1`

 **Note:** The config file is not stored in the container, because it contains stateful information in between runs that would not persist otherwise.

### Building a Docker Image

* Run `make docker-build` to build a Slappd Docker image.
* Build & run it from crontab: `*/5 * * * cd /path/to/slappd/source && make docker-run > /dev/null 2>&1`

### Installing to a Virtualenv

* Install Slappd to a virtualenv via `make install`.
* Run it from crontab: `*/5 * * * ~/.virtualenv/slappd/bin/slappd > /dev/null 2>&1`
