### modules/mission_control/main.tf
```hcl
# IoT Core Registry
resource "google_cloudiot_registry" "splat_registry" {
  name     = "${var.iot_registry_id}-${var.environment}"
  region   = var.region
  project  = var.project_id

  event_notification_configs {
    pubsub_topic_name = google_pubsub_topic.telemetry.id
    subfolder_matches = ""
  }

  state_notification_config = {
    pubsub_topic_name = google_pubsub_topic.device_state.id
  }

  mqtt_config = {
    mqtt_enabled_state = "MQTT_ENABLED"
  }

  http_config = {
    http_enabled_state = "HTTP_ENABLED"
  }
}

# Pub/Sub Topics
resource "google_pubsub_topic" "telemetry" {
  name    = "splat-telemetry-${var.environment}"
  project = var.project_id

  labels = {
    environment = var.environment
  }
}

resource "google_pubsub_topic" "device_state" {
  name    = "splat-device-state-${var.environment}"
  project = var.project_id

  labels = {
    environment = var.environment
  }
}
```
