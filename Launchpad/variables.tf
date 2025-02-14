### variables.tf
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

variable "device_certificate_path" {
  description = "Path to the device certificate file for IoT core"
  type  =  string
  default = null # optional for development
}

variable "storage_class" {
  description = "Storage class for buckets"
  type        = string
  default     = "STANDARD"
}

variable "vpc_cidr" {
  description = "The CIDR range for the VPC"
  type        = string
  default     = "10.0.0.0/16"  # Default development VPC CIDR
}

variable "ground_station_cidrs" {
  description = "List of CIDR ranges for ground stations"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Default to allow all for development
}

variable "developer_group" {
  description = "Email of the developers group"
  type        = string
  default     = "group:splat@ghostlab.net"   
}

variable "operator_group" {
  description = "Email of the operators group"
  type        = string
  default     = "group:splat@ghostlab.net"  
}

variable "devops_group" {
  description = "Email of the DevOps team group"
  type        = string
  default     = "group:splat@ghostlab.net" 
}
