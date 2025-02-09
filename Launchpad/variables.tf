### variables.tf
```hcl
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "Default region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Default zone for resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "iot_registry_id" {
  description = "IoT Core registry ID"
  type        = string
  default     = "splat-devices"
}

variable "storage_class" {
  description = "Storage class for buckets"
  type        = string
  default     = "STANDARD"
}
```
