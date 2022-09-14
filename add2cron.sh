#!/bin/bash
# add a cron job to run the tornado server every 5 minutes
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
croncmd="$SCRIPT_DIR/run.sh > /dev/null 2>&1"
cronjob="*/5 * * * * $croncmd"
# avoids duplicated insertion
( crontab -l | grep -v -F "$croncmd" ; echo "$cronjob" ) | crontab -