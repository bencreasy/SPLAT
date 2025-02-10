variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "The environment (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "region" {
  description = "The region for resources"
  type        = string
  default     = "us-central1"
}

variable "vpc_cidr" {
  description = "The CIDR range for the VPC"
  type        = string
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "ground_station_cidrs" {
  description = "List of CIDR ranges for ground stations"
  type        = list(string)
  validation {
    condition     = alltrue([for cidr in var.ground_station_cidrs : can(cidrhost(cidr, 0))])
    error_message = "All ground station CIDRs must be valid IPv4 CIDR blocks."
  }
}

variable "iot_ip_ranges" {
  description = "List of IP ranges for IoT devices"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Default to all IPs, restrict in production
}

variable "devops_group" {
  description = "Email of the DevOps team group"
  type        = string
  validation {
    condition     = can(regex("^[^@]+@[^@]+\\.[^@]+$", var.devops_group))
    error_message = "DevOps group must be a valid email address."
  }
}

variable "developer_group" {
  description = "Email of the developers group"
  type        = string
  validation {
    condition     = can(regex("^[^@]+@[^@]+\\.[^@]+$", var.developer_group))
    error_message = "Developer group must be a valid email address."
  }
}

variable "operator_group" {
  description = "Email of the operators group"
  type        = string
  validation {
    condition     = can(regex("^[^@]+@[^@]+\\.[^@]+$", var.operator_group))
    error_message = "Operator group must be a valid email address."
  }
}

variable "enable_cmek" {
  description = "Enable Customer Managed Encryption Keys"
  type        = bool
  default     = false
}

variable "enable_audit_logs" {
  description = "Enable detailed audit logging"
  type        = bool
  default     = true
}

variable "max_retention_days" {
  description = "Maximum number of days to retain logs"
  type        = number
  default     = 30
  validation {
    condition     = var.max_retention_days >= 1 && var.max_retention_days <= 3650
    error_message = "Retention days must be between 1 and 3650."
  }
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

variable "enable_private_access" {
  description = "Enable private Google Access"
  type        = bool
  default     = true
}
