#!/bin/sh
echo "This is the promote script"
repmgr standby promote -f /etc/repmgr.conf --log-to-file
ssh barman@barman barman switch-xlog --force --archive <[ host.hostname ]>
ssh barman@barman barman backup <[ host.hostname ]>