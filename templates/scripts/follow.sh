#!/bin/sh
echo "This is the follow script" >> /var/log/postgresql/postgresql-9.6-main.log
touch /var/lib/postgresql/postgresql.trigger
repmgr standby follow -f /etc/repmgr.conf --log-to-file
