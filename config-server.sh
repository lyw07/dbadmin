#!/bin/sh
ansible-playbook -i hosts get_ip.yml
ansible-playbook -i hosts barman_setup.yml
ansible-playbook -i hosts postgresql_install.yml
ansible-playbook -i hosts db_setup.yml
ansible-playbook -i hosts barman_after.yml
ansible-playbook -i hosts standby_after.yml
ansible-playbook -i hosts barman_standby.yml
