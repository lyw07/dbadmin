#!/bin/sh
echo "This is the restore script"
/usr/bin/barman-wal-restore -U barman <[ barman.hostname ]> <[ master.hostname ]> $1 $2