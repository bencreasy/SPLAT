# Mission Control - IoT Core and Pub/Sub Setup
module "mission_control" {
  source = "./modules/mission_control"

  project_id      = var.project_id
  region          = var.region
  environment     = var.environment
  iot_registry_id = var.iot_registry_id
  device_certificate_path = "${path.module}/certs/splat_dev.pem"
}

# Ground Station - Functions and Processing
module "ground_station" {
  source = "./modules/ground_station"

  project_id         = var.project_id
  region            = var.region
  environment       = var.environment
  telemetry_topic_id = module.mission_control.telemetry_topic_id
  device_state_topic_id   = module.mission_control.device_state_topic_id
  deploy_functions    = false
}

# Telemetry - Storage and Database
module "telemetry" {
  source = "./modules/telemetry"

  project_id     = var.project_id
  environment    = var.environment
  storage_class  = var.storage_class
  analyst_group_email = var.operator_group
  service_account_email = var.operator_group
}

# Security - IAM and Authentication
module "security" {
  source = "./modules/security"

  project_id   = var.project_id
  environment  = var.environment
  vpc_cidr           = var.vpc_cidr
  ground_station_cidrs = var.ground_station_cidrs
  developer_group     = var.developer_group
  operator_group      = var.operator_group
  devops_group        = var.devops_group
}
