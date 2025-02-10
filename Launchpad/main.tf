# Mission Control - IoT Core and Pub/Sub Setup
module "mission_control" {
  source = "./modules/mission_control"

  project_id      = var.project_id
  region          = var.region
  environment     = var.environment
  iot_registry_id = var.iot_registry_id
}

# Ground Station - Functions and Processing
module "ground_station" {
  source = "./modules/ground_station"

  project_id         = var.project_id
  region            = var.region
  environment       = var.environment
  pubsub_topic_id   = module.mission_control.telemetry_topic_id
  runtime  = "python39"
}

# Telemetry - Storage and Database
module "telemetry" {
  source = "./modules/telemetry"

  project_id     = var.project_id
  environment    = var.environment
  storage_class  = var.storage_class
}

# Security - IAM and Authentication
module "security" {
  source = "./modules/security"

  project_id   = var.project_id
  environment  = var.environment
}
