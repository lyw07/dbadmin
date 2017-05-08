# -*- mode: ruby -*-
# vi: set ft=ruby :
require 'fileutils'

Vagrant.require_version ">= 1.8.0"

CONFIG = File.join(File.dirname(__FILE__), "vagrant/config.rb")

$local_release_dir = "/vagrant/temp"
$forwarded_ports = {}
host_vars = {}
$num_instances = 3

if File.exist?(CONFIG)
  require CONFIG
end

# if $inventory is not set, try to use example
$inventory = File.join(File.dirname(__FILE__), "inventory") if ! $inventory

# if $inventory has a hosts file use it, otherwise copy over vars etc
# to where vagrant expects dynamic inventory to be.
if ! File.exist?(File.join(File.dirname($inventory), "hosts"))
  $vagrant_ansible = File.join(File.dirname(__FILE__), ".vagrant",
                       "provisioners", "ansible")
  FileUtils.mkdir_p($vagrant_ansible) if ! File.exist?($vagrant_ansible)
  if ! File.exist?(File.join($vagrant_ansible,"inventory"))
    FileUtils.ln_s($inventory, $vagrant_ansible)
  end
end


# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.ssh.insert_key = false
  config.vm.box = "debian/jessie64"

  (1..$num_instances).each do |machine_id|
    config.vm.define "machine#{machine_id}" do |config|
      if machine_id == 1
        ip = "192.168.33.9"
      end
      if machine_id == 2
        ip = "192.168.33.10"
      end
      if machine_id == 3
        ip = "192.168.33.11"
      end

      $forwarded_ports.each do |guest, host|
        config.vm.network "forwarded_port", guest: guest, host: host, auto_correct: true
      end
      
      config.vm.provider :virtualbox do |vb|
        vb.gui = false
        vb.memory = 1024
        vb.cpus = 1
      end

      # host_vars["machine#{machine_id}"] = {
      #   "ip": ip,
      #   "flannel_interface": ip,
      #   "flannel_backend_type": "host-gw",
      #   "local_release_dir" => $local_release_dir,
      #   "download_run_once": "False",
      #   "kube_network_plugin": "flannel",
      # }
      config.vm.network "private_network", ip: ip

      # config.vm.provision "ansible" do |ansible|
      #   ansible.playbook = "setup.yml"
      #   if File.exist?(File.join(File.dirname($inventory), "hosts"))
      #     ansible.inventory_path = $inventory
      #   end
      #   ansible.sudo = true
      #   ansible.limit = "all"
      #   # ansible.verbose = "-vvv"
      #   ansible.host_key_checking = false
      #   ansible.raw_arguments = ["--forks=#{$num_instances}"]
      #   ansible.host_vars = host_vars
      #   ansible.groups = {
      #     "barman" => ["machine1"],
      #     "postgresql" => ["machine1", "machine2"],
      #     "db" => ["machine2"],
      #     "barman(after)" => ["machine1"],
      #     # "backup" => ["machine3"],
      #   }
      # end
    end
  end
end
