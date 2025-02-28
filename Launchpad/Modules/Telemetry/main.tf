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
    action {
      type = "Delete"
    }
    }

    labels = {
      environment = var.environment
      purpose = "raw-data"
    }
  }


#Firestore is commented out for initial deployment
# Firestore 

# resource "google_firestore_database" "splat_db" {
#   project     = var.project_id
#   name        = "(default)"
#   location_id = var.firestore_location
#   type        = "FIRESTORE_NATIVE"
#
#   concurrency_mode = "OPTIMISTIC"
#
#   app_engine_integration_mode = "DISABLED"
# }

#resource "google_firestore_database" "splat_db" {
#  project     = var.project_id
#  name        = "(default)"
#  location_id = var.firestore_location
#  type        = "FIRESTORE_NATIVE"

#  concurrency_mode = "OPTIMISTIC"

#  app_engine_integration_mode = "DISABLED"
#}


# BigQuery Dataset for Analytics
resource "google_bigquery_dataset" "telemetry_analytics" {
  dataset_id                  = "splat_telemetry_${var.environment}"
  friendly_name              = "SPLAT Telemetry Analytics"
  description                = "Analytics dataset for SPLAT telemetry data"
  location                   = var.location
  project                    = var.project_id

  default_table_expiration_ms = var.analytics_retention_days * 24 * 60 * 60 * 1000

  labels = {
    environment = var.environment
    purpose     = "analytics"
  }

  access {
    role          = "OWNER"
    group_by_email = var.developer_group
  }

  access {
    role           = "READER"
    group_by_email = var.analyst_group_email
  }
}

# IAM member for BigQuery
resource "google_project_iam_member" "bigquery" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "group:${var.service_account_email}"  # Make sure this is actually a group email
}

# Create standard tables

resource "google_bigquery_table" "device_telemetry" {
  dataset_id = google_bigquery_dataset.telemetry_analytics.dataset_id
  table_id   = "device_telemetry"
  project    = var.project_id

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["device_id", "metric_type"]

  schema = file("${path.module}/schemas/device_telemetry.json")

  labels = {
    environment = var.environment
    data_type   = "telemetry"
  }
}

# Pub/Sub topic for real-time analytics

resource "google_pubsub_topic" "realtime_analytics" {
  name    = "splat-realtime-analytics-${var.environment}"
  project = var.project_id

  message_retention_duration = "86400s"  # 24 hours

  labels = {
    environment = var.environment
    purpose     = "analytics"
  }
}

# Cloud Function for data transformation

resource "google_storage_bucket" "function_source" {
  name     = "splat-telemetry-functions-${var.environment}"
  location = var.location
  project  = var.project_id

  uniform_bucket_level_access = true
}

resource "google_cloudfunctions_function" "data_transformer" {
  name        = "splat-telemetry-transformer-${var.environment}"
  description = "Transform telemetry data for analytics"
  runtime     = "python39"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_source.name
  source_archive_object = "functions/transformer.zip"
  entry_point          = "transform_telemetry"

  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.raw_data.name
  }

  environment_variables = {
    ENVIRONMENT          = var.environment
    DESTINATION_DATASET = google_bigquery_dataset.telemetry_analytics.dataset_id
    ANALYTICS_TOPIC     = google_pubsub_topic.realtime_analytics.name
  }
}

# IAM configuration

resource "google_storage_bucket_iam_member" "viewer" {
  bucket = google_storage_bucket.telemetry_data.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.service_account_email}"
}

resource "google_project_iam_member" "bigquery" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${var.service_account_email}"
}

# Monitoring and Alerting

resource "google_monitoring_alert_policy" "storage_usage" {
  display_name = "SPLAT Telemetry Storage Usage - ${var.environment}"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Storage bucket filling up"
    
    condition_threshold {
      filter          = "resource.type = \"gcs_bucket\" AND resource.labels.bucket_name = \"${google_storage_bucket.telemetry_data.name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.storage_alert_threshold

      trigger {
        count = 1
      }

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.notification_channels
}
