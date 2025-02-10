
provider "google" {
  project = kinetic-abbey-450502-d6
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = kinetic-abbey-450502-d6
  region  = var.region
  zone    = var.zone
}
