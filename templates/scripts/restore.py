#!/usr/bin/python
import os
import sys
import subprocess

# Do other things here.
print('Running restore command!')
command = '/usr/bin/barman-wal-restore -U barman barman <[ master.hostname ]> ' + sys.argv[1] + ' ' + sys.argv[2]
subprocess.check_call(command.split())