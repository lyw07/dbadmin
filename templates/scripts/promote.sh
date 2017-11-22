#!/bin/sh
echo "This is the promote script"
touch /etc/wal-e.d/env/postgresql.trigger
repmgr standby promote -f /etc/repmgr.conf --log-to-file
# WALE_GS_PREFIX="gs://teststudiobackup/" GOOGLE_APPLICATION_CREDENTIALS=/etc/wal-e.d/env/google_application_credentials.json wal-e backup-push /var/lib/postgresql/9.6/main/
