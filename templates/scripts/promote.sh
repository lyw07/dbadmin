#!/bin/sh
echo "This is the promote script"
repmgr standby promote -f /etc/repmgr.conf --log-to-file
WALE_GS_PREFIX="gs://teststudiobackup/" GOOGLE_APPLICATION_CREDENTIALS=/etc/wal-e.d/env/GOOGLE_APPLICATION_CREDENTIALS wal-e backup-push /var/lib/postgresql/9.6/main/
