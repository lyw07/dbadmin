#!/usr/bin/python
import argparse
import subprocess
import imp
import os

_script_root = os.path.dirname(os.path.realpath(__file__))
_home_dir = os.path.expanduser('~')

def _as_array(val):
    return val.split()

def _install_pystache_if_needed():
    try:
        imp.find_module('pystache')
    except:
        subprocess.check_call('sudo pip install pystache'.split(), shell=True)

def _apply_template(template_file, args, output_file):
    _install_pystache_if_needed()
    try:
        import pystache
        pystache.defaults.DELIMITERS = (u'[[', u']]')
        template = open(template_file)
        output = open(output_file, 'w')
        output.write(pystache.render(template.read(), args))
        template.close()
        output.close()
        return True
    except:
        return False

def _run_commands(commands):
    outputs = {}
    for command in commands:
        try:
            subprocess.check_call(command.split())
        except:
            return False
    return True

def terraform_handler(args):
    # Generate the terraform variables configuration file and run terraform apply
    tf_vars = {
        'project_id': args.project_id,
        'zone': args.zone,
        'region': args.region,
        'disk_type': args.disk_type,
        'disk_size': args.disk_size,
        'machine_type': args.machine_type,
        'master': {
            'hostname': args.master_hostname
        },
        'standby': []
    }
    for i in xrange(args.num_standby):
        hostname = args.standby_hostname_prefix + str(i+1)
        tf_vars['standby'].append({
            'hostname': hostname
        })
    # Generate terraform files from templates and run terraform.
    _apply_template(_home_dir + '/.dbadmin/repo/templates/terraform/main.tf', tf_vars, _home_dir + '/.dbadmin/terraform/main.tf')
    _apply_template(_home_dir + '/.dbadmin/repo/templates/terraform/output.tf', tf_vars, _home_dir + '/.dbadmin/terraform/output.tf')
    _apply_template(_home_dir + '/.dbadmin/repo/templates/terraform/variables.tf', tf_vars, _home_dir + '/.dbadmin/terraform/variables.tf')
    subprocess.check_call(_as_array(_home_dir + '/.dbadmin/bin/terraform apply ' + _home_dir + '/.dbadmin/terraform'))

    # Generate the hosts file from the output of the terraform step.
    hosts_vars = {
        'barman': {
            'hostname': 'barman',
            'external_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output barman_external_ip')).rstrip(),
            'internal_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output barman_internal_ip')).rstrip(),
        },
        'master': {
            'hostname': args.master_hostname,
            'external_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output ' + args.master_hostname + '_external_ip')).rstrip(),
            'internal_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output ' + args.master_hostname + '_internal_ip')).rstrip(),
        },
        'standby': [
        ]}
    for i in xrange(args.num_standby):
        hostname = args.standby_hostname_prefix + str(i+1)
        hosts_vars['standby'].append({
            'hostname': hostname,
            'external_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output ' + hostname + '_external_ip')).rstrip(),
            'internal_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output ' + hostname + '_internal_ip')).rstrip(),
        })
    _apply_template(_home_dir + '/.dbadmin/repo/templates/hosts', hosts_vars, _home_dir + '/.dbadmin/hosts')

    # TODO(bharadwajs) Also decompose remaining ansible playbook YAML files to support the number of replicas requested.
    ansible_commands = [
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/get_ip.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/barman_setup.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/postgresql_install.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/db_setup.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/barman_after.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/standby_after.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/barman_standby.yml'
    ]
    _run_commands(ansible_commands)

    # Fetch the list of running instances using gcloud and their ip addresses. 
    # Apply the ip address information to generate the hosts file used by ansible.
    # 

def bootstrap_handler(args):
    # Installs dependencies needed for the dbadmin tool to work.
    bootstrap_commands = [
        'sudo apt-get update',
        'sudo apt-get install -y curl python-pip build-essential libssl-dev libffi-dev python-dev',
        'sudo pip install --upgrade pip',
        'sudo pip install ansible',
        'ansible-playbook -i ' + _script_root + '/hosts -c local ' + _script_root + '/playbooks/bootstrap_admin.yml',
    ]
    _run_commands(bootstrap_commands)

parser = argparse.ArgumentParser(description="LearningEquality database administration tool.")
subparsers = parser.add_subparsers(help='Subcommand help')

bootstrap_parser = subparsers.add_parser('bootstrap', help='Installs dependencies needed by the admin tool')
bootstrap_parser.set_defaults(handler=bootstrap_handler)

terraform_parser = subparsers.add_parser('terraform', help='terraform help')
terraform_parser.add_argument('--project_id', required=True, help='The GCE project id.')
terraform_parser.add_argument('--zone', required=True, help='The GCE zone.')
terraform_parser.add_argument('--region', required=True, help='The GCE region.')
terraform_parser.add_argument('--disk_type', required=True, choices=['pd-ssd', 'pd-standard', 'local-ssd'], help='The type of the disk.')
terraform_parser.add_argument('--disk_size', required=True, help='The size of the disk.')
terraform_parser.add_argument('--machine_type', default='f1-micro', help='The machine type.')
terraform_parser.add_argument('--master_hostname', default='master', help='Host name for the master')
terraform_parser.add_argument('--standby_hostname_prefix', default='standby', help='Hostname prefix for the standby instances')
terraform_parser.add_argument('--num_standby', default=2, type=int, help='Number of standby instances')
terraform_parser.set_defaults(handler=terraform_handler)

args = parser.parse_args()
args.handler(args)