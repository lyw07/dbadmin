#!/bin/sh

ansible-playbook -i hosts barman_setup.yml -s
ansible-playbook -i hosts postgresql_install.yml -s
ansible-playbook -i hosts db_setup.yml -s
ansible-playbook -i hosts barman_after.yml -s
ansible-playbook -i hosts standby_after.yml -s
