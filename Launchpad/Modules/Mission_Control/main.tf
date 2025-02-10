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

  log_level = var.log_level

  credentials {
    public_key_certificate = {
      format      = "X509_CERTIFICATE_PEM"
      certificate = file(var.device_certificate_path)
    } : null
  }
}

# Pub/Sub Topics
resource "google_pubsub_topic" "telemetry" {
  name    = "splat-telemetry-${var.environment}"
  project = var.project_id

  message_retention_duration = "86600s"  # 24 hours

  labels = {
    environment = var.environment
    purpose     = "telemetry"
  }
}

resource "google_pubsub_topic" "device_state" {
  name    = "splat-device-state-${var.environment}"
  project = var.project_id

  labels = {
    environment = var.environment
    purpose     = "device-state"
  }
}

resource "google_pubsub_topic" "commands" {
  name    = "splat-commands-${var.environment}"
  project = var.project_id

  labels = {
    environment = var.environment
    purpose     = "commands"
  }
}

# Subscriptions
resource "google_pubsub_subscription" "telemetry_sub" {
  name    = "splat-telemetry-sub-${var.environment}"
  topic   = google_pubsub_topic.telemetry.name
  project = var.project_id

  message_retention_duration = "86400s"  # 24 hours
  retain_acked_messages     = true
  ack_deadline_seconds      = 20

  expiration_policy {
    ttl = "2592000s"  # 30 days
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"  # 10 minutes
  }

  enable_message_ordering = true
}

# Dead Letter Topics
resource "google_pubsub_topic" "dead_letter" {
  name    = "splat-dead-letter-${var.environment}"
  project = var.project_id

  labels = {
    environment = var.environment
    purpose     = "dead-letter"
  }
}
