## Back up database using Barman and Repmgr


Requirements
----------------------
* Ansible v2.3
* Vagrant v1.9.3
* VirtualBox v5.1.22
* Your ssh key must be copied to all the servers part of your inventory. To do so, change the variable value `ansible_ssh_private_key_file` in file `hosts`.

> *Note*: The oldest versions of the tools that support running the project has not been tested, but it is recommended to  update to the versions listed here.


Details of the Project
----------------------
This project uses **Vagrant** to set up four virtual machines with **debian jessie**. To know more about the settings of these four virtual machines, please take a look at the `Vagrantfile`. 

It also uses **ansible** to configure these four machines. The file `hosts` shows that machine1 is the barman server, machine2 is the master server, and machine3 and machine4 are the standby servers. 

The bash script `config-server.sh` will be run so that the machines will be configured in the order that we desire. 

The five ansible-playbooks are `barman-setup.yml` which configures barman server, `postgresql.yml` which mainly installs postgresql on the master server (machine2) and two standby servers (machine3 and machine4), `db_setup.yml` which configures the master server and two standby servers, `barman_after.yml` which start data backup of the master server in barman, `standby_after.yml` which clone the data of master server to the standby servers and start repmgrd in the standby servers.

The configuration files of the four machines are stored in the folder `config` accordingly. 



Get Started
----------------------
To run the project, 

* do `vagrant up` to set up the four virtual machines. 

* After machines are successfully built, do `./config-server.sh` to run the ansible-playbooks.

* After all the machines are configured, you can do `vagrant ssh <machineName>` to log onto the machines. 

* To check if barman has backup of the master server, do `barman list-backup pg` as a **barman** user, where **pg** is the name of the master server which is configured in barman's `pg.conf`. 

* To perform a remote backup from barman, do `barman recover --target-time "yyyy-mm-dd hh:mm:ss" --remote-ssh-command "ssh <username>@<hostname>" pg <backupID> /var/lib/postgresql/9.6/main/` as a **barman** user

* To check if the master server and the standby servers are running correctly, check the logfile in the folder `/var/log/postgresql/` to see whether standby servers get data from the master server and have **repmgrd** running.

* **[not working perfectly right now]** To test an automatic **failover**, turn down the master server by using `service postgresql stop` as a **root** user so that repmgrd in the standby servers will detect it and perform a automatic failover after 60 seconds.




