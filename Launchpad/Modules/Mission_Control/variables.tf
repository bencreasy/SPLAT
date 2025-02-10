variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "The environment (dev, staging, prod)"
  type        = string
}

variable "region" {
  description = "The region for IoT resources"
  type        = string
  default     = "us-central1"
}

variable "iot_registry_id" {
  description = "The ID for the IoT registry"
  type        = string
}

variable "log_level" {
  description = "The default logging level"
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["NONE", "ERROR", "INFO", "DEBUG"], var.log_level)
    error_message = "Log level must be one of: NONE, ERROR, INFO, DEBUG."
  }
}

variable "device_certificate_path" {
  description = "Path to the device certificate file"
  type        = string
  default = null # optional for development
}
