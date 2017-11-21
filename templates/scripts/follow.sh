#!/bin/sh
echo "This is the follow script"
# sleep 30  # Let promote command finish so that follow command can find the new master node
repmgr standby follow -f /etc/repmgr.conf --log-to-file --upstream-node-id=%n
