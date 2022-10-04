#!/bin/bash

# current script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# change to working dir
cd $SCRIPT_DIR

# check if tornado server is running
if /usr/bin/pgrep -f "tornado-server" > /dev/null
then
    echo "Stopping tornado server..."
    /usr/bin/pkill -f "tornado-server" 
fi
