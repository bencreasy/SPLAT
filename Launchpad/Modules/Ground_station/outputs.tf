output "function_service_account" {
  description = "The email of the function service account"
  value       = google_service_account.function_account.email
}

output "processed_data_bucket" {
  description = "The name of the processed data bucket"
  value       = google_storage_bucket.processed_data.name
}

output "analytics_dataset" {
  description = "The ID of the BigQuery analytics dataset"
  value       = google_bigquery_dataset.analytics.dataset_id
}
