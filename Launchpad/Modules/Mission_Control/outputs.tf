output "registry_id" {
  description = "The ID of the IoT registry"
  value       = google_cloudiot_registry.splat_registry.id
}

output "telemetry_topic_id" {
  description = "The ID of the telemetry topic"
  value       = google_pubsub_topic.telemetry.id
}

output "device_state_topic_id" {
  description = "The ID of the device state topic"
  value       = google_pubsub_topic.device_state.id
}

output "commands_topic_id" {
  description = "The ID of the commands topic"
  value       = google_pubsub_topic.commands.id
}
```
