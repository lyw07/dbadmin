#!/usr/bin/python
import argparse
import subprocess
import imp

_bootstrap_commands = [
    'sudo apt-get install -y unzip python-pip build-essential libssl-dev libffi-dev python-dev',
    'pip install --upgrade pip',
    'sudo pip install ansible pystache',
    'curl https://releases.hashicorp.com/terraform/0.9.6/terraform_0.9.6_linux_amd64.zip > /tmp/terraform.zip',
    'mkdir .dbadmin',
    'mkdir .dbadmin/bin',
    'unzip /tmp/terraform.zip -d ./.dbadmin/bin',
    'mkdir .dbadmin/repo',
    'git clone http://github.com/bsubrama/backupdb.git ./.dbadmin/repo',
    'cp ./.dbadmin/repo/terraform ./.dbadmin/terraform',
    'cp ./.dbadmin/repo/playbooks ./.dbadmin/playbooks',
    'cp ./.dbadmin/repo/config ./.dbadmin/config',
]

_terraform_commands = [
    './.dbadmin/bin/terraform apply ./.dbadmin/terraform'
]

def _install_pystache_if_needed():
    try:
        imp.find_module('pystache')
    except:
        subprocess.check_call('sudo pip install pystache'.split())

def _apply_template(template_file, args, output_file):
    install_pystache_if_needed()
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
    }
    _apply_template('./.dbadmin/repo/templates/terraform/variables.tf', tf_vars, './.dbadmin/terraform/variables.tf')
    _run_commands(_terraform_commands)

def bootstrap_handler(args):
    # Installs dependencies needed for the dbadmin tool to work.
    # Stops on the first error.
    _run_commands(_bootstrap_commands)

parser = argparse.ArgumentParser(description="LearningEquality database administration tool.")
subparsers = parser.add_subparsers(help='Subcommand help')

bootstrap_parser = subparsers.add_parser('bootstrap', help='Installs dependencies needed by the admin tool')
bootstrap_parser.set_defaults(handler=bootstrap_handler)

terraform_parser = subparsers.add_parser('terraform', help='terraform help')
terraform_parser.add_argument('--project_id', required=True, help='The GCE project id.')
terraform_parser.add_argument('--zone', required=True, help='The GCE zone.')
terraform_parser.add_argument('--region', required=True, help='The GCE region.')
terraform_parser.add_argument('--disk_type', required=True, choices=['pd-ssd', 'pd-hdd', 'local-ssd'], help='The type of the disk.')
terraform_parser.add_argument('--disk_size', required=True, help='The size of the disk.')
terraform_parser.add_argument('--machine_type', default='f1-micro', help='The machine type.')
terraform_parser.set_defaults(handler=terraform_handler)

args = parser.parse_args()
args.handler(args)