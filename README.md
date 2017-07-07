## dbadmin - Administration Tool For Replicated Postgres Setups

The `dbadmin` tool implements playbooks to support common replicated database administration functions for Postgres, including:

- Terraforming instances
- Configuring Postgres failover clusters and backup using repmgr and barman
- Restoring a master node from a sqldump
- Safely bringing up a failed master node as a standby
- Setting up a testing server that contains a snapshot of master server's data

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

The `terraform-instances` function terraforms instances according to the provided arguments that specify the region, zone, machine type, disk type, disk size and optionally the replica hostname prefix, the number of replicas and the testing server hostname. It then generates the `.dbadmin/playbooks/terraform_instances.yml` file from the `templates/terraform_instances.yml` file using commandline flags and environment variables, and executes the playbook using `ansible-playbook`. This creates the instances using the `terraform` tool, configures ssh access to them and creates a `.dbadmin/terraform.tfstate` file which would be needed by subsequent `terraform` calls to have a map of the current state of the setup. Hence it is important to keep this file safe. 

*Example*: 
* To set up the barman server and three replicas including one master and two standbys, please do `backupdb/dbadmin.py terraform-instances --project_id <project_id> --zone <zone> --region <region> --disk_type <disk type> --disk_size <disk size> --num_replicas=3`. 

* To set up a testing server, please do `backupdb/dbadmin.py terraform-instances --project_id <project_id> --zone <zone> --region <region> --disk_type <disk_type> --disk_size <disk_size> --num_replicas=3 --testing --testing_hostname=<testing_server_hostname>` where <project_id>, <zone>, <region>, <disk_type>, <disk_size> and number of replicas should be the same as the values when setting up barman server and three replicas. You can run the command along with or after setting up the barman server and three replicas.

> *Note*: You can also choose to set up a testing server not through `dbadmin.py terraform-instance` but directly creating on Google Cloud Platform. Please go to *dbadmin.py fork-database* to see instructions for this case.

**dbadmin.py configure-instances**

The `configure-instances` function configures the terraformed instances by:

- Installing dependencies (postgresql-9.6, barman, repmgr, among others);
- Setting passwordless ssh and sudoers for appropriate users;
- Generating and copying configuration files for `barman` and `repmgr` from templates under `templates/config`;
- Setting up `barman` backup for all replicas;
- Setting up Postgres streaming replication between the master and the standbys;
- Setting up `repmgr` master and standbys and bringing up the entire cluster.

At the end of this function, you should have a fully-functioning master-standby failover setup, and you can start using the database at this point. Note that the `configure-instances` function sets up the first replica as the master. 

*Example*:
To configure the barman server and replicas, please do `backupdb/dbadmin.py configure-instances --num_replicas=3` where the number of replicas should be the same as the one set in *dbadmin.py terraform-instances*

**dbadmin.py restore-database**

The `restore-database` function allows you to restore data to the master from a sqldump located on a Google Cloud Storage bucket. At the end of the run, the data from the sqldump file will be imported into the master; the tool assumes that streaming replication has already been set up, so the standbys should catch up with the master. 

**dbadmin.py reinit-standby**

The `reinit-standby` function allows the administrator to safely bring up a failed master as a standby (after repmgr has handled the failover).

*Example*:
To bring up a failed master as a standby, please do `dbadmin.py reinit-standby --instance_hostname=<failed_master_hostname> --master_hostname=<current_master_hostname> --num_replicas=<number_of_replicas>` where number of replicas includes the failed master server.

**dbadmin.py fork-database**

The `fork-database` function configures the testing server which is set up through *dbadmin.py terraform-instances* or directly through Google Cloud Platform. It updates the ansible inventory with values related to the testing server, installs dependecies and transfer the current master server's up-to-date data that is stored in barman to the testing server.

*Example*:
*If the testing server is set up through *dbadmin.py terraform-instances*, please do `dbadmin.py fork-database --master_hostname=<current_master_hostname> --num_replicas=<number_of_replicas> --testing_hostname=<testing_server_hostname> --testing_terraformed` where the number of replicas should be the same as the value set up in terraform.

* If the testing server is set up directly through Google Cloud Platform, please do `dbadmin.py fork-database --master_hostname=<current_master_hostname> --num_replicas=<number_of_replicas> --testing_hostname=<testing_server_hostname> --testing_external_ip=<testing_server_external_ip> --testing_internal_ip=<testing_server_internal_ip>`.

Get Started
----------------------
To set up the tool:

* Bring up a VM instance on Google Compute Engine configured to use a service account with the privileges described above.
 
* After the instance is successfully built, install git using `sudo apt-get install -y git`.

* Clone the backupdb project using `git clone http://github.com/lyw07/backupdb.git`. This shoudl create a directory `backupdb` in your home directory containing the tool.

* Run the bootstrap function using `backupdb/dbadmin.py bootstrap --iam_account=<service-account>`. This should set up the `.dbadmin` directory in your home directory that will be expected by subsequent operations, and also install other dependencies. 

Other Notes
------------------------

* To check if barman has backup of the master server, do `barman list-backup pg` as a **barman** user, where **replica1** is the name of the master server which is configured in barman's `replica1.conf`. 

* To perform a remote backup from barman, do `barman recover --target-time "yyyy-mm-dd hh:mm:ss" --remote-ssh-command "ssh <username>@<hostname>" <master_server> <backupID> /var/lib/postgresql/9.6/main/` as a **barman** user

* To check if the master server and the standby servers are running correctly, check the logfile in the folder `/var/log/postgresql/` to see whether standby servers get data from the master server and have **repmgrd** running.

* To test an automatic **failover**, turn down the master server by using `service postgresql stop` as a **root** user so that repmgrd in the standby servers will detect it and perform a automatic failover after 15 seconds. Assuming the instances are `replica1`, `replica2` and `replica3`, and `replica1` is the current master, repmgrd will promote `replica2` to become a new master and let `replica3` follow `replica2`.
	* To check if automatic failover works correctly, 
		* log into standby server as user *postgres*
		* run `psql`
		* connect to database `repmgr` as user `repmgr` by typing `\c repmgr repmgr`
		* do `SELECT * FROM repmgr_replicas.repl_nodes ORDER BY id;` to see if standby2's *upstream_node_id* is now 2 instead of 1
		* or do `SELECT * FROM repmgr_replicas.repl_events;` to see if *promote* and *follow* have been done.
	* In order to let barman connect to the cluster again, 
		* do `barman backup replica2` in the barman server.

