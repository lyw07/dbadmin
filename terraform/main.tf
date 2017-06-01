provider "google" {
	region = "${var.region}"
	project = "${var.project_name}"
  // Uncomment if running from a local machine
  // credentials = "${file(var.account_file_path)}"
}

// create a new barman instance
resource "google_compute_instance" "barman" {
  name = "barman"
  zone = "${var.zone}"
  machine_type = "${var.machine_type}"
  disk {
    image = "debian-8-jessie-v20170426"
    type = "pd-hdd"
    size = "${var.disk_size}"
  }

  network_interface {
    network = "default"

    access_config {
      nat_ip =""
    }
  }
}

// create a new master instance
resource "google_compute_instance" "master" {
  name = "master"
  zone = "${var.zone}"
  machine_type = "${var.machine_type}"

  disk {
    image = "debian-8-jessie-v20170426"
    type = "${var.disk_type}"
    size = "${var.disk_size}"
  }

  network_interface {
    network = "default"

    access_config {
      nat_ip =""
    }
  } 
}

// create a new standby instance
resource "google_compute_instance" "standby1" {
  name = "standby1"
  zone = "${var.zone}"
  machine_type = "${var.machine_type}"
  
  disk {
    image = "debian-8-jessie-v20170426"
    type = "${var.disk_type}"
    size = "${var.disk_size}"
  }

  network_interface {
    network = "default"

    access_config {
      nat_ip =""
    }
  } 
}

// create a second standby instance
resource "google_compute_instance" "standby2" {
  name = "standby2"
  zone = "${var.zone}"
  machine_type = "${var.machine_type}"
  
  disk {
    image = "debian-8-jessie-v20170426"
    type = "${var.disk_type}"
    size = "${var.disk_size}"
  }

  network_interface {
    network = "default"

    access_config {
      nat_ip =""
    }
  } 
}