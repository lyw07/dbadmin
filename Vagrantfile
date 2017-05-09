# -*- mode: ruby -*-
# vi: set ft=ruby :

$forwarded_ports = {}
$num_instances = 3


Vagrant.configure("2") do |config|

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

      config.vm.network "private_network", ip: ip
    end
  end
end
