#!/bin/bash


NAME=sphinxlogzabbixmonitor
PIDFILE=/var/run/$NAME.pid


if [ -f $PIDFILE ]; then
	echo "$PIDFILE already exists"
	exit 0
fi

PID=`nohup python /opt/sphinx_new/python/script/monitor_query_log_zabbix_trap.py -l $1 -c $2 > $3 2>&1 & echo $!`

if [ -z $PIDFILE ]; then
	print "Fail"
else 
	echo $PID > $PIDFILE
	echo $PID

fi 