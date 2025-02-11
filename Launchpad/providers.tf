
provider "google" {
  project = "kinetic-abbey-450502-d6"
  region  = var.region
  zone    = var.zone
  credentials = "${path.module}/splat-key.json"
}

provider "google-beta" {
  project = "kinetic-abbey-450502-d6"
  region  = var.region
  zone    = var.zone
}
