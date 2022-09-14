#!/bin/bash

# run tornado server.py script if not already running
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# change to working dir
cd $SCRIPT_DIR

# check if tornado server is running
if ! /usr/bin/pgrep -f "tornado-server" > /dev/null
then
    echo "Starting tornado server..."
    /usr/bin/nohup $SCRIPT_DIR/tornado-server.py > $SCRIPT_DIR/tornado-server.log 2>&1 &
else
    echo "Tornado server already running..."
fi
