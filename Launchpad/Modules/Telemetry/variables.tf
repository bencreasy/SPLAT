### modules/telemetry/variables.tf
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "The environment (dev, staging, prod)"
  type        = string
}

variable "location" {
  description = "The location for resources"
  type        = string
  default     = "US"
}

variable "storage_class" {
  description = "The storage class for the telemetry bucket"
  type        = string
  default     = "STANDARD"
}

variable "archive_age_days" {
  description = "Days before data is moved to coldline storage"
  type        = number
  default     = 90
}

variable "delete_age_days" {
  description = "Days before data is deleted"
  type        = number
  default     = 365
}

variable "analytics_retention_days" {
  description = "Days to retain analytics data"
  type        = number
  default     = 180
}

variable "firestore_location" {
  description = "Location for Firestore database"
  type        = string
  default     = "nam5"
}

variable "analyst_group_email" {
  description = "Google Group email for analysts"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for accessing telemetry data"
  type        = string
}

variable "storage_alert_threshold" {
  description = "Storage usage threshold for alerts (percentage)"
  type        = number
  default     = 80
}

variable "notification_channels" {
  description = "List of notification channel IDs"
  type        = list(string)
  default     = []
}
