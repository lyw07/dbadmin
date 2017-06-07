output "barman_internal_ip" {
    value = "${google_compute_instance.barman.*.network_interface.0.address}"
}

output "barman_external_ip" {
    value = "${google_compute_instance.barman.*.network_interface.0.access_config.0.assigned_nat_ip}"
}

<[ #version_stable ]>
output "<[ master.hostname ]>_internal_ip" {
    value = "${google_compute_instance.<[ master.hostname ]>.*.network_interface.0.address}"		
}		
		
output "<[ master.hostname ]>_external_ip" {		
    value = "${google_compute_instance.<[ master.hostname ]>.*.network_interface.0.access_config.0.assigned_nat_ip}"		
}		
		
<[ #standby ]>
output "<[ hostname ]>_internal_ip" {
    value = "${google_compute_instance.<[ hostname ]>.*.network_interface.0.address}"
}	
        
output "<[ hostname ]>_external_ip" {
    value = "${google_compute_instance.<[ hostname ]>.*.network_interface.0.access_config.0.assigned_nat_ip}"
}
<[ /standby ]>

<[ #version_stable ]>
<[ #version_alpha ]>
<[ #replicas ]>
output "<[ hostname ]>_internal_ip" {
    value = "${google_compute_instance.<[ hostname ]>.*.network_interface.0.address}"
}

output "<[ hostname ]>_external_ip" {
    value = "${google_compute_instance.<[ hostname ]>.*.network_interface.0.access_config.0.assigned_nat_ip}"
}
<[ /replicas ]>
<[ /version_alpha ]>