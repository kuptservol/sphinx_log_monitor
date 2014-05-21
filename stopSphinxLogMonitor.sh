#!/bin/bash

NAME=sphinxlogzabbixmonitor
PIDFILE=/var/run/$NAME.pid

printf "Stopping $NAME... "
PID=`cat $PIDFILE`
if [ -f $PIDFILE ]; then
	kill -TERM $PID
	echo "killed $PID"
	rm -f $PIDFILE
else
	echo "$PIDFILE not found"
fi
