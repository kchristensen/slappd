# slappd

### Features
A basic Slack integration for Untappd. It will notify the Slack channel you've specified:

![Screenshot](screenshot.png)

### Configuration
* Install the required Python modules via: `pip -r requirements.txt`
* Edit the [untappd.cfg](untappd.cfg) example provided to reflect your API information
* Run it from crontab: `*/5 * * * python /path/to/untappd.py > /dev/null 2>&1`
