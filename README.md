SphinxLogMonitor
================

Make a simple daemon to monitor sphinx query params through Zabbix

Installing

1.) Install zabbix-agent

 tar -xzvf zabbix-1.6.2.tar.gz
 cd zabbix-1.6.2
 ./configure --enable-agent --prefix=/usr/local/zabbix
 make install


2.) Download files from repository

3.) make sh executable
chmod +x startSphinxLogMonitor.sh
chmod +x stopSphinxLogMonitor.sh

4.) start  ./startSphinxLogMonitor.sh
Usage:
./startSphinxLogMonitor.sh <querylog_path> <zabbix_config_path> <sh_log>

<querylog_path> - path to query.log
<zabbix_config_path> - path to zabbix_conf.ini

