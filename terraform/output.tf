output "barman" {
    value = "${join("\n", google_compute_instance.barman.*.network_interface.0.address, google_compute_instance.barman.*.network_interface.0.access_config.0.assigned_nat_ip)}"
}

output "master" {
    value = "${join("\n", google_compute_instance.master.*.network_interface.0.address, google_compute_instance.master.*.network_interface.0.access_config.0.assigned_nat_ip)}"
}

output "standby1" {
    value = "${join("\n", google_compute_instance.standby1.*.network_interface.0.address, google_compute_instance.standby1.*.network_interface.0.access_config.0.assigned_nat_ip)}"
}

output "standby2" {
    value = "${join("\n", google_compute_instance.standby2.*.network_interface.0.address, google_compute_instance.standby2.*.network_interface.0.access_config.0.assigned_nat_ip)}"
}