### modules/telemetry/main.tf
```hcl
# Cloud Storage Buckets
resource "google_storage_bucket" "telemetry_data" {
  name     = "splat-telemetry-${var.environment}"
  location = "US"
  project  = var.project_id

  uniform_bucket_level_access = true
  storage_class              = var.storage_class

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
}

# Firestore
resource "google_firestore_database" "splat_db" {
  project     = var.project_id
  name        = "(default)"
  location_id = "nam5"
  type        = "FIRESTORE_NATIVE"

  concurrency_mode = "OPTIMISTIC"
}
```
