#!/usr/bin/python

__author__ = "skuptsov"

import subprocess
import re
import os
import sys
import getopt
from signal import *
import ConfigParser
import logging
import datetime
from threading import Thread

procList = []
log_parse_pattern = ''
pattern = None
log_monitor_command_pref = ''
zabbix_trap_cmd_pref = ''
zabbix_trapcmd_pattern = '%s -z %s -s "%s" -p %s'
zabbixKeyLogFieldMapping = {}
currentTimeAggregationSlot = None
timeAggregationPeriodSec = 0


logging.basicConfig(filename='query_zabbix.log',level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
            
class TimeAggreationSlot:

    def __init__(self):
        self.time = datetime.datetime.now()

    time = None
    indexValuesSumMap = {} 
    indexValuesCount = {}



def processObjectTimeAggregation(index, keyValueMap):
    global currentTimeAggregationSlot
    if  currentTimeAggregationSlot == None:
        currentTimeAggregationSlot = TimeAggreationSlot()
        currentTimeAggregationSlot.indexValuesSumMap = {index : keyValueMap}
        currentTimeAggregationSlot.indexValuesCount = {index : 1}
    else:
        if datetime.datetime.now() - currentTimeAggregationSlot.time < datetime.timedelta(seconds=timeAggregationPeriodSec) :
            if index in currentTimeAggregationSlot.indexValuesSumMap:
                currentKeyValueMap = currentTimeAggregationSlot.indexValuesSumMap[index]
                currentTimeAggregationSlot.indexValuesCount[index]+=1
                number = currentTimeAggregationSlot.indexValuesCount[index]
                for key in keyValueMap:
                    #put ariphmetic avg
                    currentKeyValueMap[key]= (number-1)*currentKeyValueMap[key]/number+ keyValueMap[key]/number
            else:
                currentTimeAggregationSlot.indexValuesSumMap.update({index : keyValueMap})
                currentTimeAggregationSlot.indexValuesCount.update({index : 1})
        else:
            for key in currentTimeAggregationSlot.indexValuesSumMap:
                m = currentTimeAggregationSlot.indexValuesSumMap[key]
                for key2 in m:   
                    trapZabbixNewThread(key2, m[key2]) 
   
            currentTimeAggregationSlot =  TimeAggreationSlot()
            currentTimeAggregationSlot.indexValuesSumMap = {index : keyValueMap}
            currentTimeAggregationSlot.indexValuesCount = {index : 1}

    logging.debug(currentTimeAggregationSlot.indexValuesSumMap)
 


def runProc(process_command, mode, processLineFunction, saveProc):
    logging.debug('starting process : '+process_command)
    for line in runProcess(process_command.split(), saveProc):
        logging.debug(line)
        processLineFunction(line)

def runProcess(exe, saveProc):    
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if saveProc == True:
        procList.append(p)    
    
    while(True):
        retcode = p.poll() 
        line = p.stdout.readline()
        yield line
        if(retcode is not None):
            break

def processLine(line):
    matcher = pattern.match(line)
    processObject(matcher)

def processObject(matcher):
    
    if matcher != None:
        index = matcher.group('index')
        if index in zabbixKeyLogFieldMapping:
            map = zabbixKeyLogFieldMapping[matcher.group('index')]
            keyValueMap = {}
            for key in map:
                value = float(matcher.group(key))
                if value != None:
                    keyValueMap[map[key]] = value
            processObjectTimeAggregation(index, keyValueMap)


def trapZabbixNewThread(key, value):
    thread = Thread(target = trapZabbix, args = (key, value))
    thread.start()

def emptyFunction(line):
    pass

def trapZabbix(key, value):
    
    zabbix_trap_cmd = zabbix_trap_cmd_pref + ' -k %s -o %s -vv --real-time' % (key, value)

    runProc(zabbix_trap_cmd, None, emptyFunction, False)

def main(argv):
    querylog_path = ''
    zabbix_config_path  = ''


    try:
        opts, args = getopt.getopt(argv,"l:c:",["log=","conf="])
    except getopt.GetoptError:
        printUsage()
    for opt, arg in opts:
        if opt in ("-l", "--log"):
           querylog_path = arg
           if querylog_path is None:
               printUsage()
        elif opt in ("-c", "--conf"):
           zabbix_config_path = arg
           if zabbix_config_path is None:
               printUsage()


    logging.info('LOG_FILE   :' + querylog_path)
    logging.info('CONF_FILE   :' + zabbix_config_path)

    parseConfig(zabbix_config_path)

    print('starting monitoring process...')
      
    runProc(log_monitor_command_pref % (querylog_path), None, processLine, True)


def printUsage():
    print 'usage: monitor_query_log_zabbix_trap.py -l <querylog_path> -c <zabbix_config_path>'
    sys.exit(2)

def parseConfig(zabbix_config_path):
    zabbix_config = ConfigParser.ConfigParser()
    zabbix_config.read(zabbix_config_path)

    zabbix_server_host = zabbix_config.get("ZabbixServer", "zabbix_server_host")   
    source_host_name = zabbix_config.get("ZabbixServer", "source_host_name") 
    zabbix_trap_port = zabbix_config.get("ZabbixServer", "zabbix_trap_port") 
    zabbix_sender_path = zabbix_config.get("ZabbixServer", "zabbix_sender_path") 

    global zabbix_trap_cmd_pref, log_parse_pattern, log_monitor_command_pref, zabbixKeyLogFieldMapping, pattern, timeAggregationPeriodSec

    zabbix_trap_cmd_pref = zabbix_trapcmd_pattern % (zabbix_sender_path,zabbix_server_host,source_host_name,zabbix_trap_port)
    log_parse_pattern = zabbix_config.get("LogMonitor", "log_parse_pattern")
    timeAggregationPeriodSec = float(zabbix_config.get("LogMonitor", "time_aggregation_period_sec"))
    pattern = re.compile(log_parse_pattern)
    log_monitor_command_pref = zabbix_config.get("LogMonitor", "log_monitor_command_pref")

    indexKeyLogMap = getSectionMap( zabbix_config, "ZabbixKeyLogFieldMapping")

    for key in indexKeyLogMap.keys():
        value = indexKeyLogMap[key]
        map = eval(value)
        zabbixKeyLogFieldMapping[key] = map
    

def getSectionMap(config, section):
    dict = {}
    options = config.options(section)
    for option in options:
        try:
            dict[option] = config.get(section, option)
            if dict[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            logging.error("exception on %s!" % option)
            dict[option] = None
    return dict

def clean(*args):
    print('stopping monitoring process...')
    for proc in procList:
        try :
            os.kill(proc.pid, SIGTERM)
        except Exception, e :
            logging.error("Error while killing subprocess : ")
            logging.error(str(e))
    sys.exit(0)

if __name__ == "__main__":
    for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM):
        signal(sig, clean)
    main(sys.argv[1:])
