#!/usr/bin/python

import subprocess
import re
import sys
import getopt
from pysnmp.entity.rfc3413.oneliner import cmdgen

pattern = re.compile('.*ios=(?P<ios>[\d.]+) kb=(?P<kb>[\d.]+) ioms=(?P<ioms>[\d.]+) cpums=(?P<cpums>[\d.]+)')
process_command_pref = 'tail -f'

cmdGen = cmdgen.CommandGenerator()

def runProcess(exe):    
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        retcode = p.poll() #returns None while subprocess is running
        line = p.stdout.readline()
        yield line
        if(retcode is not None):
            break

def processLine(line):
    matcher = pattern.match(line)
    buildObject(matcher)

def buildObject(matcher):
    if matcher != None:
        cpums = matcher.group("cpums")
        ioms = matcher.group("ioms")
        kb = matcher.group("kb")
        ios = matcher.group("ios")
        setSMTPParam('', ioms)

def runProc(process_command, mode):
    for line in runProcess(process_command.split()):
        print line
        processLine(line)

def main(argv):
    querylog_path = ''
    mode = ''

    try:
      opts, args = getopt.getopt(argv,"f:m",["log=","mode="])
    except getopt.GetoptError:
      print 'usage: monitor_query_log.py -f <querylog_path> -m <mode=(snmp|)>'
      sys.exit(2)
    for opt, arg in opts:
      if opt in ("-f", "--log"):
         querylog_path = arg
      elif opt in ("-m", "--mode"):
          mode = arg

    print 'LOG_FILE   :', querylog_path
    print 'MODE   :', mode
      
    runProc(process_command_pref + ' ' + querylog_path, mode)

#move method to another file
def setSMTPParam(param_name, param_value):
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.setCmd(
        cmdgen.CommunityData('public'),
        cmdgen.UdpTransportTarget(('demo.snmplabs.com', 161)),
        (cmdgen.MibVariable('SNMPv2-MIB', 'sysORDescr', 1), param_value)
    )

    # Check for errors and print out results
    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1] or '?'
                )
            )
        else:
            for name, val in varBinds:
               print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
         

if __name__ == "__main__":
    setSMTPParam('param_name', 180)
    setSMTPParam('param_name', 40)	
    main(sys.argv[1:])

    