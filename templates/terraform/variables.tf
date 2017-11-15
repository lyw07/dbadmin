variable "region" {
  description = "The region of the Google Cloud Project"
  default = "<[ region ]>"
}

variable "zone" {
	description = "The zone of the resource"
    default = "<[ zone ]>"
}

variable "machine_type" {
	description = "Machine type of the Google Compute Instance"
    default = "<[  machine_type ]>"
}

variable "project_id" {
  description = "The ID of the Google Cloud Project"
  default = "<[ project_id ]>"
}

variable "disk_type" {
  description = "The disk type to be used"
  default = "<[ disk_type ]>"
}

variable "disk_size" {
  description = "The disk size to be used"
  default = "<[ disk_size ]>"
}

// Uncomment if running locally
// variable "account_file_path" {
//   description = "Path to the JSON file used to describe your account credentials"
// }
