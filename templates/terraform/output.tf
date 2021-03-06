<[ #replicas ]>
output "<[ hostname ]>_internal_ip" {
    value = "${google_compute_instance.<[ hostname ]>.*.network_interface.0.address}"
}

output "<[ hostname ]>_external_ip" {
    value = "${google_compute_instance.<[ hostname ]>.*.network_interface.0.access_config.0.assigned_nat_ip}"
}
<[ /replicas ]>

<[ #staging ]>
output "<[ hostname ]>_internal_ip" {
    value = "${google_compute_instance.<[ hostname ]>.*.network_interface.0.address}"
}
output "<[ hostname ]>_external_ip" {
    value = "${google_compute_instance.<[ hostname ]>.*.network_interface.0.access_config.0.assigned_nat_ip}"
}
<[ /staging ]>
