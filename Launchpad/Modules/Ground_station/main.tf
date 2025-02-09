### modules/ground_station/main.tf
```hcl
# Cloud Functions
resource "google_cloudfunctions_function" "data_processor" {
  name        = "splat-processor-${var.environment}"
  description = "SPLAT data processing function"
  runtime     = var.function_runtime
  
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_source.name
  source_archive_object = google_storage_bucket_object.function_zip.name
  entry_point          = "process_telemetry"
  
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = var.pubsub_topic_id
  }

  environment_variables = {
    ENVIRONMENT = var.environment
  }
}

# Function source bucket
resource "google_storage_bucket" "function_source" {
  name     = "splat-functions-${var.environment}"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
}
```
