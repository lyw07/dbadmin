provider "google" {
	region = "${var.region}"
	project = "${var.project_id}"
  // Uncomment if running from a local machine
  // credentials = "${file(var.account_file_path)}"
}

<[ #replicas ]>
// create <[ hostname ]> instance
resource "google_compute_instance" "<[ hostname ]>" {
  name = "<[ hostname ]>"
  zone = "${var.zone}"
  machine_type = "${var.machine_type}"
  
  disk {
    image = "debian-8-jessie-v20171025"
    type = "${var.disk_type}"
    size = "${var.disk_size}"
  }

  network_interface {
    network = "default"

    access_config {
      nat_ip =""
    }
  }

  service_account {
    email = "wal-e-backups@contentworkshop-159920.iam.gserviceaccount.com",
    scopes = ["useraccounts-ro", "storage-rw", "logging-write", "monitoring-write", "service-management", "service-control", "https://www.googleapis.com/auth/pubsub", "https://www.googleapis.com/auth/trace.append", "compute-ro"]
  } 
}
<[ /replicas ]>

<[ #staging ]>
// create <[ hostname ]> instance
resource "google_compute_instance" "<[ hostname ]>" {
  name = "<[ hostname ]>"
  zone = "${var.zone}"
  machine_type = "${var.machine_type}"
  
  disk {
    image = "debian-8-jessie-v20171025"
    type = "${var.disk_type}"
    size = "${var.disk_size}"
  }

  network_interface {
    network = "default"

    access_config {
      nat_ip =""
    }
  }

  service_account {
    email = "wal-e-backups@contentworkshop-159920.iam.gserviceaccount.com",
    scopes = ["useraccounts-ro", "storage-rw", "logging-write", "monitoring-write", "service-management", "service-control", "https://www.googleapis.com/auth/pubsub", "https://www.googleapis.com/auth/trace.append", "compute-ro"]
  } 
}
<[ /staging ]>

resource "google_compute_instance_group" "cluster" {
  name = "test-wale-backup-cluster"
  description = "Cluster containing db management instance and replicas"

  instances = [
    <[ #replicas ]>
    "${google_compute_instance.<[ hostname ]>.self_link}",
    <[ /replicas ]>
  ]

  named_port {
    name = "postgres"
    port = "5432"
  }

  zone = "${var.zone}"
}
