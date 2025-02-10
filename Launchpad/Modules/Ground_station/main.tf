# Cloud Functions for data processing
resource "google_storage_bucket" "function_source" {
  name          = "splat-functions-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = true

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# Function ZIP files
resource "google_storage_bucket_object" "function_zip" {
  count = var.deploy_functions ? 1 : 0
  name   = "function_source/data_processor-${filemd5("../../function_source/data_processor.zip")}.zip"
  bucket = google_storage_bucket.function_source.name
  source = "../../functions/data_processor.zip"
}

resource "google_storage_bucket_object" "alert_zip" {
  count = var.deploy_functions ? 1 : 0
  name   = "function_source/alert_processor-${filemd5("../../function_source/alert_processor.zip")}.zip"
  bucket = google_storage_bucket.function_source.name
  source = "../../functions/alert_processor.zip"
}

# Main data processing function
resource "google_cloudfunctions_function" "data_processor" {
  name        = "splat-processor-${var.environment}"
  description = "Process incoming SPLAT telemetry data"
  runtime     = "python39"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_source.name
  source_archive_object = google_storage_bucket_object.function_zip.name
  entry_point          = "process_telemetry"
  
  environment_variables = {
    ENVIRONMENT = var.environment
    PROJECT_ID  = var.project_id
  }

  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = var.telemetry_topic_id
  }

  service_account_email = google_service_account.function_account.email
}

# Alert processing function
resource "google_cloudfunctions_function" "alert_processor" {
  name        = "splat-alerts-${var.environment}"
  description = "Process SPLAT alerts and notifications"
  runtime     = "python39"

  available_memory_mb   = var.function_memory
  source_archive_bucket = google_storage_bucket.function_source.name
  source_archive_object = google_storage_bucket_object.alert_zip.name
  entry_point          = "process_alert"

  environment_variables = {
    ENVIRONMENT = var.environment
    PROJECT_ID  = var.project_id
  }

  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = var.device_state_topic_id
  }

  service_account_email = google_service_account.function_account.email
}

# Service Account for functions
resource "google_service_account" "function_account" {
  account_id   = "splat-function-${var.environment}"
  display_name = "SPLAT Function Service Account"
  project      = var.project_id
}

# IAM bindings for service account
resource "google_project_iam_member" "function_invoker" {
  project = var.project_id
  role    = "roles/cloudfunctions.invoker"
  member  = "serviceAccount:${google_service_account.function_account.email}"
}

resource "google_project_iam_member" "pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.function_account.email}"
}

# Storage for processed data
resource "google_storage_bucket" "processed_data" {
  name          = "splat-processed-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = var.data_retention_days
    }
    action {
      type = "Delete"
    }
  }

  versioning {
    enabled = true
  }
}

# BigQuery dataset for analytics
resource "google_bigquery_dataset" "analytics" {
  dataset_id  = "splat_analytics_${var.environment}"
  project     = var.project_id
  location    = var.region
  description = "SPLAT analytics data"

  default_table_expiration_ms = var.data_retention_days * 24 * 60 * 60 * 1000

  labels = {
    environment = var.environment
  }
}
