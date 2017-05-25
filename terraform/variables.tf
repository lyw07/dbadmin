variable "region" {
  default = "us-central"
}

variable "zone" {
	default = "us-central1-c"	
}

variable "machine_type" {
	default = "f1-micro"
}

variable "project_name" {
  description = "The ID of the Google Cloud Project"
  default = "testing-168423"
}

variable "account_file_path" {
  description = "Path to the JSON file used to describe your account credentials"
  default = "testing-4e08eebba610.json"
}