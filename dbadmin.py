#!/usr/bin/python
import argparse
import subprocess
import imp
import os

_script_root = os.path.dirname(os.path.realpath(__file__))
_working_root = os.path.expanduser('~') + '/.dbadmin'
_template_root = _script_root + '/templates'

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

def _apply_template_and_run_playbook(playbook, vars, hosts, debug=False, local=False):
    _apply_template(_template_root + '/playbooks/' + playbook + '.yml', vars, _working_root + '/playbooks/' + playbook + '.yml')
    _run_commands(['ansible-playbook ' + ('-vvvv -i ' if debug else '-i ') + hosts + ' ' + ('-c local ' if local else '') + _working_root + '/playbooks/' + playbook + '.yml'])

def terraform_instances_handler(args):
    # Generate the terraform variables configuration file and run terraform apply
    tf_vars = {
        'project_id': args.project_id,
        'zone': args.zone,
        'region': args.region,
        'disk_type': args.disk_type,
        'disk_size': args.disk_size,
        'machine_type': args.machine_type,
    }
    tf_vars['replicas'] = []
    for i in xrange(args.num_replicas):
        hostname = args.replica_hostname_prefix + str(i+1)
        tf_vars['replicas'].append({
            'hostname': hostname,
        })
    # Generate terraform files from templates and run terraform.
    _apply_template(_template_root + '/terraform/main.tf', tf_vars, _working_root + '/terraform/main.tf')
    _apply_template(_template_root + '/terraform/output.tf', tf_vars, _working_root + '/terraform/output.tf')
    _apply_template(_template_root + '/terraform/variables.tf', tf_vars, _working_root + '/terraform/variables.tf')
    _apply_template_and_run_playbook('terraform_instances', tf_vars, local=True, hosts=_script_root + '/hosts', debug=args.debug)

def configure_instances_handler(args):
    # Generate the hosts file from the output of the terraform step.
    hosts_vars = {
        'barman': {
            'hostname': 'barman',
            'external_ip': subprocess.check_output(_as_array(_working_root + '/bin/terraform output --state=' + _working_root + '/terraform.tfstate barman_external_ip')).rstrip(),
            'internal_ip': subprocess.check_output(_as_array(_working_root + '/bin/terraform output --state=' + _working_root + '/terraform.tfstate  barman_internal_ip')).rstrip(),
        },
        'standby': [
        ],
        'replicas': [
        ]}
    for i in xrange(args.num_replicas):
        hostname = args.replica_hostname_prefix + str(i+1)
        vars = {
            'hostname': hostname,
            'external_ip': subprocess.check_output(_as_array(_working_root + '/bin/terraform output --state=' + _working_root + '/terraform.tfstate ' + hostname + '_external_ip')).rstrip(),
            'internal_ip': subprocess.check_output(_as_array(_working_root + '/bin/terraform output --state=' + _working_root + '/terraform.tfstate ' + hostname + '_internal_ip')).rstrip(),
            'index': str(i+1)
        }
        hosts_vars['replicas'].append(vars)
        if i == 0:
            hosts_vars['master'] = vars
        else:
            hosts_vars['standby'].append(vars)
    _apply_template(_template_root + '/hosts', hosts_vars, _working_root + '/hosts')

    # Generate configuration files needed for configuring the instances.
    for replica in hosts_vars['replicas']:
        vars = {
            'host': replica,
            'barman': hosts_vars['barman'],
            'app_server': {
                'internal_ip': args.appserver_internalip
            },
            'master': hosts_vars['master'],
        }
        host_config_dir = _working_root + '/config/' + replica['hostname']
        if not os.path.exists(host_config_dir):
            os.makedirs(host_config_dir)
        _apply_template(_template_root + '/config/barman/replica.conf', vars, _working_root + '/config/barman/' + replica['hostname'] + '.conf')
        _apply_template(_template_root + '/config/replica/pg_hba.conf', vars, host_config_dir + '/pg_hba.conf')
        _apply_template(_template_root + '/config/replica/postgresql.conf', vars, host_config_dir + '/postgresql.conf')
        _apply_template(_template_root + '/config/replica/repmgr.conf', vars, host_config_dir + '/repmgr.conf')
        script_dir = _working_root + '/scripts'
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
        _apply_template(_template_root + '/scripts/restore.py', vars, script_dir + '/restore.py')

    # Generate the playbook for configuring the replicas, and run it.
    _apply_template_and_run_playbook('configure_instances', hosts_vars, hosts=_working_root + '/hosts', debug=args.debug)

def restore_database_handler(args):
    # Run the sql import on the master if the corresponding flags have been set.
    if args.sqldump_location and args.sqldump_location.find(':') > 0:
        db_import_vars = {
            'dbname': args.database_name,
            'dbuser': args.database_user,
            'db_import_bucket': args.sqldump_location.split(':')[0],
            'db_import_path': args.sqldump_location.split(':')[1],
            'master': {
                'hostname': args.master_hostname
            }
        }
        _apply_template_and_run_playbook('restore_database', db_import_vars, hosts=_working_root + '/hosts', debug=args.debug)
    else:
        print('Location of sqldump on Google Cloud Storage for initializing the database must be in the form [storage-bucket]:[path/to/sql/file].')

def reinit_standby_handler(args):
    # Destroy the instance and recreate it the terraform configuration files.
    vars = {
        'replica': {
            'hostname': args.standby_hostname,
        },
        'master': {
            'hostname': args.master_hostname,
        },
        'gcs_bucket': args.gcs_bucket,
    }
    _apply_template_and_run_playbook('reinit_standby', vars, hosts=_working_root + '/hosts', debug=args.debug)

def status_handler(args):
    _apply_template_and_run_playbook('status', {}, hosts=_working_root + '/hosts', debug=args.debug)

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
    vars = { 'service_account': args.iam_account }
    _apply_template_and_run_playbook('bootstrap_admin', vars, _script_root + '/hosts', debug=args.debug, local=True)

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
configure_instances_parser.add_argument('--appserver_internalip', default=None, help='Internal IP address of the app server that will talk to the replicas.')

restore_database_parser = subparsers.add_parser('restore-database', help='Restores the master from a sqldump stored in a Google Compute Storage bucket.')
restore_database_parser.set_defaults(handler=restore_database_handler)
restore_database_parser.add_argument('--master_hostname', required=True, help='Hostname of the current master.')
restore_database_parser.add_argument('--database_name', required=True, help='Name of the database to be created.')
restore_database_parser.add_argument('--database_user', required=True, help='Name of the user to be created to access postgres.')
restore_database_parser.add_argument('--sqldump_location', required=True, help='Location of sqldump on Google Cloud Storage for initializing the database, in the form [storage-bucket]:[path/to/sql/file].')

status_parser = subparsers.add_parser('status', help='Show the current status of the setup.')
status_parser.set_defaults(handler=status_handler)

reinit_standby_parser = subparsers.add_parser('reinit-standby', help='Brings down a failed master and adds it back as a standby to the current configuration.')
reinit_standby_parser.add_argument('--standby_hostname', required=True, help='Hostname of the failed master to be added back as a standby.')
reinit_standby_parser.add_argument('--master_hostname', required=True, help='Hostname of the current master.')
reinit_standby_parser.add_argument('--gcs_bucket', help='Optional bucket to backup the failed master\'s data directory before recreating it.')
reinit_standby_parser.set_defaults(handler=reinit_standby_handler)

parser.add_argument('--version', default='stable', choices=['alpha', 'stable'], help='Version of dbadmin.py behavior.')
parser.add_argument('--debug', default=False, type=bool, help='Show debug info or not.')

args = parser.parse_args()
args.handler(args)