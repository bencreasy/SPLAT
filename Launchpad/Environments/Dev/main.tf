terraform {
  required_version = ">= 1.0.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }

  backend "gcs" {
    bucket = "splat-terraform-state-dev"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "mission_control" {
  source = "../../modules/mission_control"

  project_id      = var.project_id
  environment     = var.environment
  iot_registry_id = var.iot_registry_id
}
