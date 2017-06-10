## dbadmin Postgres Replicated Database Administration Tool

The `dbadmin` tool implements playbooks to support common replicated database administration functions for Postgres, including:

- Terraforming instances
- Configuring Postgres failover clusters and backup using repmgr and barman
- Restoring a master node from a sqldump
- Safely bringing up a failed master node as a standby

`dbadmin` is designed to work with Google Compute Engine only. Vagrant support is as yet untested.

Requirements
----------------------
- Debian jessie
- git
- gcloud gsutil

All other dependencies are automatically pulled in when running `dbadmin.py bootstrap`. These dependencies include:

- Downloaded Binaries: terraform
- Apt Dependencies: gcsutil barman repmgr postgres-9.6 python-2.7 python-pip
- Pip Dependencies: ansible pystache psycopg2 pexpect

Additionally, the instance in which `dbadmin` runs should have a service account with the following permissions enabled:

- Service Account Actor
- Project Owner
- ???

> *Note*: The oldest versions of the tools that support running the project has not been tested, but it is recommended to  update to the versions listed here.

Details of the Project
----------------------

The `dbadmin` tool generates playbooks that define the sequence of steps needed for handling various administrative operations from pre-defined templates and executes them
using `ansible-playbook`. All generated playbooks, configuration files, terraform files reside within the `.dbadmin` directory created under the home directory of the caller. Note that subsequent runs of the `dbadmin` tool may alter the contents of the `.dbadmin` directory as the tool is run; as such, contents of the `.dbadmin` directory should not be relied upon for any reason. Within the templates, contents within `<[` and `]>` are meant to be replaced by the `dbadmin` tool during its rendering process. 

The functionality of the tool for each of the supported commands is described below.

**dbadmin.py bootstrap**

The `bootstrap`function assumes the least in terms of available dependencies, and explicitly installs the minimum needed for the tool to get going. This includes installing
`python-2.7`, `ansible`, `terraform` and other dependencies required to render templates and run playbooks. It then generates the `.dbadmin/playbooks/boostrap_admin.yml` file from
the `templates/bootstrap_admin.yml` file using commandline flags and environment variables, and executes the playbook using `ansible-playbook`. This creates the directories under `.dbadmin` that are expected by subsequent steps and configures `gcloud` to start using the provided service account for its operations. 

**dbadmin.py terraform-instances**

The `terraform-instances` function terraforms instances according to the provided arguments that specify the region, zone, machine type, disk type, disk size and optionally the replica hostname prefix and the number of replicas. It then generates the `.dbadmin/playbooks/terraform_instances.yml` file from the `templates/terraform_instances.yml` file using commandline flags and environment variables, and executes the playbook using `ansible-playbook`. This creates the instances using the `terraform` tool, configures ssh access to them and creates a `.dbadmin/terraform.tfstate` file which would be needed by subsequent `terraform` calls to have a map of the current state of the setup. Hence it is important to keep this file safe. 

**dbadmin.py configure-instances**

The `configure-instances` function configures the terraformed instances by:

- Installing dependencies (postgresql-9.6, barman, repmgr, among others);
- Setting passwordless ssh and sudoers for appropriate users;
- Generating and copying configuration files for `barman` and `repmgr` from templates under `templates/config`;
- Setting up `barman` backup for all replicas;
- Setting up Postgres streaming replication between the master and the standbys;
- Setting up `repmgr` master and standbys and bringing up the entire cluster.

At the end of this function, you should have a fully-functioning master-standby failover setup, and you can start using the database at this point. Note that the `configure-instances` function sets up the first replica as the master. 

**dbadmin.py restore-database**

The `restore-database` function allows you to restore data to the master from a sqldump located on a Google Cloud Storage bucket. At the end of the run, the data from the sqldump file will be imported into the master; the tool assumes that streaming replication has already been set up, so the standbys should catch up with the master. 

**dbadmin.py reinit-standby**

The `reinit-standby` functions allows the administrator to safely bring up a failed master as a standby (after repmgr has handled the failover).

Get Started
----------------------
To set up the tool:

* Bring up a VM instance on Google Compute Engine configured to use a service account with the privileges described above.
 
* After the instance is successfully built, install git using `sudo apt-get install -y git`.

* Clone the backupdb project using `git clone http://github.com/bsubrama/backupdb.git --branch=gce`. This shoudl create a directory `backupdb` in your home directory containing the tool.

* Run the bootstrap function using `backupdb/dbadmin.py bootstrap-admin --iam_account=<service-account>`. This should set up the `.dbadmin` directory in your home directory that will be expected by subsequent operations, and also install other dependencies. 

Other Notes
------------------------

* To check if barman has backup of the master server, do `barman list-backup pg` as a **barman** user, where **pg** is the name of the master server which is configured in barman's `pg.conf`. 

* To perform a remote backup from barman, do `barman recover --target-time "yyyy-mm-dd hh:mm:ss" --remote-ssh-command "ssh <username>@<hostname>" pg <backupID> /var/lib/postgresql/9.6/main/` as a **barman** user

* To check if the master server and the standby servers are running correctly, check the logfile in the folder `/var/log/postgresql/` to see whether standby servers get data from the master server and have **repmgrd** running.

* To test an automatic **failover**, turn down the master server by using `service postgresql stop` as a **root** user so that repmgrd in the standby servers will detect it and perform a automatic failover after 15 seconds. Assuming the instances are `replica1`, `replica2` and `replica3`, and `replica1` is the current master, repmgrd will promote `replica2` to become a new master and let `replica3` follow `replica2`.
	* To check if automatic failover works correctly, 
		* log into standby server as user *postgres*
		* run `psql`
		* connect to database `repmgr` as user `repmgr` by typing `\c repmgr repmgr`
		* do `SELECT * FROM repmgr_pg.repl_nodes ORDER BY id;` to see if standby2's *upstream_node_id* is now 2 instead of 1
		* or do `SELECT * FROM repmgr_pg.repl_events;` to see if *promote* and *follow* have been done.
	* In order to let barman connect to the cluster again, 
		* do `barman backup replica2` in the barman server
		* change the names of the cluster in `repmgr.conf` to be standby1 to match with the database host name in barman
		* In `repmgr.conf`, change `restore_command` to be `/usr/bin/barman-wal-restore -U barman <barman_hostname> replica2 %f %p`.




