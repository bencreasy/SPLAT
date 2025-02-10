# Main security configuration
terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# Network Configuration
resource "google_compute_network" "splat_vpc" {
  name                            = "splat-network-${var.environment}"
  auto_create_subnetworks        = false
  delete_default_routes_on_create = true
  project                        = var.project_id
}

resource "google_compute_subnetwork" "splat_subnet" {
  name                     = "splat-subnet-${var.environment}"
  ip_cidr_range           = var.vpc_cidr
  network                 = google_compute_network.splat_vpc.id
  region                  = var.region
  project                 = var.project_id
  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata            = "INCLUDE_ALL_METADATA"
  }
}

# Service Accounts

## Device Service Account
resource "google_service_account" "device_sa" {
  account_id   = "splat-device-${var.environment}"
  display_name = "SPLAT Device Service Account - ${var.environment}"
  project      = var.project_id
}

resource "google_project_iam_member" "device_sa_roles" {
  for_each = toset([
    "roles/cloudiot.deviceController",
    "roles/pubsub.publisher"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.device_sa.email}"
}

## Ground Station Service Account
resource "google_service_account" "ground_station_sa" {
  account_id   = "splat-ground-${var.environment}"
  display_name = "SPLAT Ground Station Service Account - ${var.environment}"
  project      = var.project_id
}

resource "google_project_iam_member" "ground_station_sa_roles" {
  for_each = toset([
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/cloudiot.provisioner",
    "roles/storage.objectViewer",
    "roles/monitoring.metricWriter"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.ground_station_sa.email}"
}

## Cloud Functions Service Account
resource "google_service_account" "functions_sa" {
  account_id   = "splat-functions-${var.environment}"
  display_name = "SPLAT Functions Service Account - ${var.environment}"
  project      = var.project_id
}

resource "google_project_iam_member" "functions_sa_roles" {
  for_each = toset([
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    "roles/bigquery.dataEditor"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}

## Monitoring Service Account
resource "google_service_account" "monitoring_sa" {
  account_id   = "splat-monitoring-${var.environment}"
  display_name = "SPLAT Monitoring Service Account - ${var.environment}"
  project      = var.project_id
}

resource "google_project_iam_member" "monitoring_sa_roles" {
  for_each = toset([
    "roles/monitoring.viewer",
    "roles/monitoring.metricWriter",
    "roles/logging.viewer",
    "roles/logging.configWriter"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.monitoring_sa.email}"
}

# IAM Group Assignments

## DevOps Team
resource "google_project_iam_member" "devops_roles" {
  for_each = toset([
    "roles/owner",
    "roles/iam.securityReviewer",
    "roles/monitoring.admin"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "group:${var.devops_group}"
}

## Developers
resource "google_project_iam_member" "developer_roles" {
  for_each = toset([
    "roles/editor",
    "roles/cloudiot.admin",
    "roles/monitoring.viewer"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "group:${var.developer_group}"
}

## Operators
resource "google_project_iam_member" "operator_roles" {
  for_each = toset([
    "roles/viewer",
    "roles/monitoring.viewer",
    "roles/logging.viewer"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "group:${var.operator_group}"
}

# VPC Firewall Rules
resource "google_compute_firewall" "allow_iot" {
  name    = "allow-iot-${var.environment}"
  network = google_compute_network.splat_vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["8883", "443"]  # MQTT and HTTPS
  }

  source_ranges = var.iot_ip_ranges
  target_tags   = ["iot-device"]
}

resource "google_compute_firewall" "allow_ground_station" {
  name    = "allow-ground-station-${var.environment}"
  network = google_compute_network.splat_vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["22", "443", "3000", "8086"]
  }

  source_ranges = var.ground_station_cidrs
  target_tags   = ["ground-station"]
}

resource "google_compute_firewall" "allow_internal" {
  name    = "allow-internal-${var.environment}"
  network = google_compute_network.splat_vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }
  allow {
    protocol = "icmp"
  }

  source_ranges = [var.vpc_cidr]
  target_tags   = ["internal"]
}

# Cloud KMS Configuration for Encryption
resource "google_kms_key_ring" "splat_keyring" {
  count    = var.enable_cmek ? 1 : 0
  name     = "splat-keyring-${var.environment}"
  location = var.region
  project  = var.project_id
}

resource "google_kms_crypto_key" "splat_key" {
  count           = var.enable_cmek ? 1 : 0
  name            = "splat-key-${var.environment}"
  key_ring        = google_kms_key_ring.splat_keyring[0].id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = true
  }
}
