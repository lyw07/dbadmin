#!/bin/sh
ansible-playbook -i hosts playbooks/get_ip.yml
ansible-playbook -i hosts playbooks/barman_setup.yml
ansible-playbook -i hosts playbooks/postgresql_install.yml
ansible-playbook -i hosts playbooks/db_setup.yml
ansible-playbook -i hosts playbooks/barman_after.yml
ansible-playbook -i hosts playbooks/standby_after.yml
ansible-playbook -i hosts playbooks/barman_standby.yml
