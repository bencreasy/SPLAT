### modules/telemetry/main.tf

# Cloud Storage Buckets
resource "google_storage_bucket" "telemetry_data" {
  name     = "splat-telemetry-${var.environment}"
  location = var.location
  project  = var.project_id

  uniform_bucket_level_access = true
  storage_class              = var.storage_class

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = var.archive_age_days
    }
    action {
      type = "Delete"
      
    }
  }
  labels = {
    environment = var.environment
    purpose = "telemetry"
  }
}

resource "google_storage_bucket" "raw_data" {
  name = "splat-raw-${var.environment}"
  location = var.location
  project = var.project_id

  uniform_bucket_level_access = true
  storage_class = "STANDARD"

  lifecycle_rule {
    condition {
      age = 7
    }
    acton {
      type = "Delete:
    }
    }

    labels = {
      environment = var.environment
      purpose = "raw-data"
    }
  }
}

# Firestore
resource "google_firestore_database" "splat_db" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  concurrency_mode = "OPTIMISTIC"

  app_engine_integration_mode = "Disabled"
}