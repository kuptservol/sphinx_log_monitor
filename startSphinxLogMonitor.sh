#!/bin/bash


NAME=sphinxlogzabbixmonitor
PIDFILE=/var/run/$NAME.pid

display_usage() { 
	echo -e "\nUsage:\n$0 <querylog_path> <zabbix_config_path> <sh_log> \n" 
	} 

if [ -f $PIDFILE ]; then
	echo "$PIDFILE already exists"
	exit 0
fi

if [[ ( $# == "--help") ||  $# == "-h" ]] 
	then 
		display_usage
		exit 0
fi 

if [  $# -le 1 ] 
	then 
		display_usage
		exit 1
fi

[ $# -eq 0 ] && { echo "Usage: $0 argument"; exit 1; }

PID=`nohup python monitor_query_log_zabbix_trap.py -l $1 -c $2 > $3 2>&1 & echo $!`

if [ -z $PIDFILE ]; then
	print "Fail"
else 
	echo $PID > $PIDFILE
	echo $PID

fi 
