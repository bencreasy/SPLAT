### modules/telemetry/outputs.tf
output "telemetry_bucket_name" {
  description = "The name of the telemetry storage bucket"
  value       = google_storage_bucket.telemetry_data.name
}

output "raw_bucket_name" {
  description = "The name of the raw data bucket"
  value       = google_storage_bucket.raw_data.name
}

output "analytics_dataset_id" {
  description = "The ID of the BigQuery analytics dataset"
  value       = google_bigquery_dataset.telemetry_analytics.dataset_id
}

output "firestore_database_id" {
  description = "The ID of the Firestore database"
  value       = google_firestore_database.splat_db.id
}

output "realtime_analytics_topic" {
  description = "The name of the realtime analytics Pub/Sub topic"
  value       = google_pubsub_topic.realtime_analytics.name
}

output "function_service_account" {
  description = "The service account used by the transformer function"
  value       = google_cloudfunctions_function.data_transformer.service_account_email
}
