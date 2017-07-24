Zabbix
======
Scripts and templates for Zabbix 3.0.x (other versions with LLD support should also work but they are not tested)

- In scripts you will find Bash scripts used by some LLD rules and User Parameters (need to be installed on agent)
- In sudoers.d you can find settings for sudo
- In Templates there are XML files ready to import using Zabbix GUI
- In zabbix_agentd.conf.d there are custom UserParameters (need to be installed on agent)

Templates was tested on Debian 8.x Jessie. Sometimes you need to use ```sudo``` for ```system.run[]``` or ```LLD rules```. All rules are in file ```sudoers.d/zabbix```.

Please let us know if you have any questions or concerns.

# Table of contents
-----
1. Templates
   * [Nginx](#template-microimpuls-app-nginx)
   * [Disk](#template-microimpuls-disc)
   * [Network](#template-microimpuls-network)
   * [PVR](#template-microimpuls-pvr)
   * [Redis](#template-microimpuls-redis)
   * [Smarty](#template-microimpuls-smarty)
   * [System](#template-microimpuls-system)

-----

## Template Microimpuls App nginx
Monitoring for Nginx. It is using script ```nginx-check.sh```. Add macros {$NGINX_STATS_URL} localhost:8080/nginx-stats. Add nginx config nginx/conf.d/nginx-stats.

## Template Microimpuls Disk
Monitoring for disk usage and performance. You will need to install sysstat package. 

## Template Microimpuls Network
Monitoring for network. Interface traffic and errors. Netstat TCP statistics.

## Template Microimpuls PVR
Monitoring for Microimpuls PVR. 

## Template Microimpuls Redis
Monitoring for Redis. 

## Template Microimpuls Smarty
Monitoring for Microimpuls Smarty Middleware. 

## Template Microimpuls System
Monitoring for some system stuff (cpu, memory, uwsgi socket, processes and threads. You will need to install monitoring-plugins-basic package to monitor socket response time). 

