# slappd

### About
Since Untappd does not currently support callbacks or webhooks, I wrote a basic
Slack integration that will relay check-ins for specified users on your feed to
a Slack channel.

![Screenshot](screenshot.png)

This is designed to be run from crontab, and issues one API call per run.

### Known Issues
The first time you run the script, it may be a little chatty because it has not
previously seen your feed before.

### Requirements
* Python
* Some Python modules (ConfigParser, simplejson, requests)
* A way of periodically running this script (at, cron, etc)
* Untappd [API access](https://untappd.com/api/register?register=new)
* A Slack channel full of beer lovers

### Configuration
* Install the required Python modules via: `pip install -r requirements.txt`
* Edit the [untappd.cfg](untappd.cfg) example provided to reflect your API information
* Run it from crontab: `*/5 * * * python /path/to/untappd.py > /dev/null 2>&1`
