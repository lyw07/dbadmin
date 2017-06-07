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
        pystache.defaults.DELIMITERS = (u'<[', u']>')
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

def terraform_instances_handler(args):
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
        'standby': [],
        'replicas': []
    }
    for i in xrange(args.num_standby):
        hostname = args.standby_hostname_prefix + str(i+1)
        tf_vars['standby'].append({
            'hostname': hostname
        })
    for i in xrange(args.num_replicas):
        hostname = args.replica_hostname_prefix + str(i+1)
        tf_vars['replicas'].append({
            'hostname': hostname,
        })
    # Generate terraform files from templates and run terraform.
    _apply_template(_home_dir + '/.dbadmin/repo/templates/terraform/main.tf', tf_vars, _home_dir + '/.dbadmin/terraform/main.tf')
    _apply_template(_home_dir + '/.dbadmin/repo/templates/terraform/output.tf', tf_vars, _home_dir + '/.dbadmin/terraform/output.tf')
    _apply_template(_home_dir + '/.dbadmin/repo/templates/terraform/variables.tf', tf_vars, _home_dir + '/.dbadmin/terraform/variables.tf')
    subprocess.check_call(_as_array(_home_dir + '/.dbadmin/bin/terraform apply --state=' + _home_dir + '/.dbadmin/terraform.tfstate ' + _home_dir + '/.dbadmin/terraform'))

def configure_instances_handler(args):
    # Generate the hosts file from the output of the terraform step.
    hosts_vars = {
        'barman': {
            'hostname': 'barman',
            'external_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output --state=' + _home_dir + '/.dbadmin/terraform.tfstate barman_external_ip')).rstrip(),
            'internal_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output --state=' + _home_dir + '/.dbadmin/terraform.tfstate  barman_internal_ip')).rstrip(),
        },
        'master': {
            'hostname': args.master_hostname,
            'external_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output --state=' + _home_dir + '/.dbadmin/terraform.tfstate ' + args.master_hostname + '_external_ip')).rstrip(),
            'internal_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output --state=' + _home_dir + '/.dbadmin/terraform.tfstate ' + args.master_hostname + '_internal_ip')).rstrip(),
        },
        'standby': [
        ],
        'replicas': [
        ]}
    for i in xrange(args.num_standby):
        hostname = args.standby_hostname_prefix + str(i+1)
        hosts_vars['standby'].append({
            'hostname': hostname,
            'external_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output --state=' + _home_dir + '/.dbadmin/terraform.tfstate ' + hostname + '_external_ip')).rstrip(),
            'internal_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output --state=' + _home_dir + '/.dbadmin/terraform.tfstate ' + hostname + '_internal_ip')).rstrip(),
        })
    for i in xrange(args.num_replicas):
        hostname = args.replica_hostname_prefix + str(i+1)
        vars = {
            'hostname': hostname,
            'external_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output --state=' + _home_dir + '/.dbadmin/terraform.tfstate ' + hostname + '_external_ip')).rstrip(),
            'internal_ip': subprocess.check_output(_as_array(_home_dir + '/.dbadmin/bin/terraform output --state=' + _home_dir + '/.dbadmin/terraform.tfstate ' + hostname + '_internal_ip')).rstrip(),
            'index': str(i)
        }
        hosts_vars['replicas'].append(vars)
        if i == 0:
            hosts_vars['master'] = vars
        else:
            hosts_vars['standby'].append(vars)
    _apply_template(_home_dir + '/.dbadmin/repo/templates/hosts', hosts_vars, _home_dir + '/.dbadmin/hosts')

    # Generate configuration files needed for configuring the instances.
    for replica in hosts_vars['replicas']:
        vars = {
            'host': replica,
            'barman': hosts_vars['barman'],
            'app_server': {
                'internal_ip': args.appserver_internalip
            }
        }
        _apply_template(_home_dir + '/.dbadmin/repo/templates/config/barman/replica.conf', vars, _home_dir + '/.dbadmin/config/barman/' + replica['hostname'] + '.conf')
        _apply_template(_home_dir + '/.dbadmin/repo/templates/config/replica/pg_hba.conf', vars, _home_dir + '/.dbadmin/config/' + replica['hostname'] + '/pg_hba.conf')
        _apply_template(_home_dir + '/.dbadmin/repo/templates/config/replica/postgresql.conf', vars, _home_dir + '/.dbadmin/config/' + replica['hostname'] + '/postgresql.conf')
        _apply_template(_home_dir + '/.dbadmin/repo/templates/config/replica/repmgr.conf', vars, _home_dir + '/.dbadmin/config/' + replica['hostname'] + '/repmgr.conf')

    # TODO(bharadwajs) Generate the necessary playbooks for configuring the replicas.

    # TODO(bharadwajs) Also decompose remaining ansible playbook YAML files to support the number of replicas requested.
    ansible_commands = [
        'ansible-playbook -i ' + _script_root + '/hosts -c local ' + _script_root + '/playbooks/terraform_after.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/get_ip.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/barman_setup.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/postgresql_install.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/db_setup.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/barman_after.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/standby_after.yml',
        'ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/barman_standby.yml'
    ]
    _run_commands(ansible_commands)

def initialize_master_handler(args):
    # Run the sql import on the master if the corresponding flags have been set.
    import_commands = []
    if args.database_name and args.database_user:
        db_create_args = {
            'dbname': args.database_name,
            'dbuser': args.database_user,
        }
        _apply_template(_home_dir + '/.dbadmin/repo/templates/playbooks/db_create.yml', db_create_args, _home_dir + '/.dbadmin/playbooks/db_create.yml')
        import_commands.append('ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/db_create.yml')
        if args.sqldump_location and args.sqldump_location.find(':') > 0:
            db_create_args.update({
                'db_import_bucket': args.sqldump_location.split(':')[0],
                'db_import_path': args.sqldump_location.split(':')[1]
            })
            _apply_template(_home_dir + '/.dbadmin/repo/templates/playbooks/db_import.yml', db_create_args, _home_dir + '/.dbadmin/playbooks/db_import.yml')
            import_commands.append('ansible-playbook -i ' + _home_dir + '/.dbadmin/hosts ' + _home_dir + '/.dbadmin/playbooks/db_import.yml')
    _run_commands(import_commands)

def add_standby_handler(args):
    pass

def bootstrap_handler(args):
    # Install and update pip, curl and other dependencies so that _apply_template can be run.
    bootstrap_commands = [
        'sudo apt-get update',
        'sudo apt-get install -y curl python-pip build-essential libssl-dev libffi-dev python-dev',
        'sudo pip install --upgrade pip',
        'sudo pip install ansible pystache'
    ]
    _run_commands(bootstrap_commands)

    # Generate the bootstrap playbook and run it.
    _apply_template(_script_root + '/templates/playbooks/bootstrap_admin.yml', { 'service_account': args.iam_account }, _script_root + '/playbooks/bootstrap_admin.yml')
    _run_commands(['ansible-playbook -i ' + _script_root + '/hosts -c local ' + _script_root + '/playbooks/bootstrap_admin.yml'])

parser = argparse.ArgumentParser(description="LearningEquality database administration tool.")
subparsers = parser.add_subparsers(help='Supported commands')

bootstrap_parser = subparsers.add_parser('bootstrap', help='Installs dependencies needed by the admin tool')
bootstrap_parser.add_argument('--iam_account', required=True, help='The service account in the form <service-account-id>@<project-id>.iam.gserviceaccount.com.')
bootstrap_parser.set_defaults(handler=bootstrap_handler)

terraform_instances_parser = subparsers.add_parser('terraform-instances', help='Only create instances. No configuration is done.')
terraform_instances_parser.set_defaults(handler=terraform_instances_handler)
terraform_instances_parser.add_argument('--project_id', required=True, help='The GCE project id.')
terraform_instances_parser.add_argument('--zone', required=True, help='The GCE zone.')
terraform_instances_parser.add_argument('--region', required=True, help='The GCE region.')
terraform_instances_parser.add_argument('--disk_type', required=True, choices=['pd-ssd', 'pd-standard', 'local-ssd'], help='The type of the disk.')
terraform_instances_parser.add_argument('--disk_size', required=True, help='The size of the disk.')
terraform_instances_parser.add_argument('--machine_type', default='f1-micro', help='The machine type.')
terraform_instances_parser.add_argument('--master_hostname', default='master', help='Host name for the master.')
terraform_instances_parser.add_argument('--standby_hostname_prefix', default='standby', help='Hostname prefix for the standby instances.')
terraform_instances_parser.add_argument('--num_standby', default=2, type=int, help='Number of standby instances.')
terraform_instances_parser.add_argument('--replica_hostname_prefix', default='replica', help='Hostname prefix for the instances.')
terraform_instances_parser.add_argument('--num_replicas', default=0, type=int, help='Number of replicas.')

configure_instances_parser = subparsers.add_parser('configure-instances', help='Configure instances. Assumes instances have already been created, and a tfstate file exists.')
configure_instances_parser.set_defaults(handler=configure_instances_handler)
configure_instances_parser.add_argument('--master_hostname', default='master', help='Host name for the master.')
configure_instances_parser.add_argument('--standby_hostname_prefix', default='standby', help='Hostname prefix for the standby instances.')
configure_instances_parser.add_argument('--num_standby', default=2, type=int, help='Number of standby instances.')
configure_instances_parser.add_argument('--replica_hostname_prefix', default='replica', help='Hostname prefix for the instances.')
configure_instances_parser.add_argument('--num_replicas', default=0, type=int, help='Number of replicas.')
configure_instances_parser.add_argument('--appserver_internalip', required=True, help='Internal IP address of the app server that will talk to the replicas.')

initialize_master_parser = subparsers.add_parser('initialize-master', help='Initialize the master from a sqldump stored in a Google Compute Storage bucket.')
initialize_master_parser.set_defaults(handler=initialize_master_handler)
initialize_master_parser.add_argument('--database_name', required=True, help='Name of the database to be created.')
initialize_master_parser.add_argument('--database_user', required=True, help='Name of the user to be created to access postgres.')
initialize_master_parser.add_argument('--sqldump_location', required=True, help='Location of sqldump on Google Cloud Storage for initializing the database, in the form [storage-bucket]:[path/to/sql/file].')

add_standby_parser = subparsers.add_parser('add-standby', help='Adds another standby to the current configuration.')
add_standby_parser.set_defaults(handler=add_standby_handler)

args = parser.parse_args()
args.handler(args)