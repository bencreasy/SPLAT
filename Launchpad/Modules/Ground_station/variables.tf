variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "The environment (dev, staging, prod)"
  type        = string
}

variable "region" {
  description = "The region for resources"
  type        = string
  default     = "us-central1"
}
variable "deploy_functions" {
  description = "to deploy, or not to deploy..."
  type        = bool
  default     = false
}
variable "function_memory" {
  description = "Memory allocation for Cloud Functions (MB)"
  type        = number
  default     = 256
}

variable "telemetry_topic_id" {
  description = "The ID of the telemetry Pub/Sub topic"
  type        = string
}

variable "device_state_topic_id" {
  description = "The ID of the device state Pub/Sub topic"
  type        = string
}

variable "data_retention_days" {
  description = "Number of days to retain processed data"
  type        = number
  default     = 30
}
