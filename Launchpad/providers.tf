
provider "google" {
  project = "kinetic-abbey-450502-d6"
  region  = var.region
  zone    = var.zone
  credentials = file("C:\Users\ben\Downloads\kinetic-abbey-450502-d6-b32c7c308785.json")
}

provider "google-beta" {
  project = "kinetic-abbey-450502-d6"
  region  = var.region
  zone    = var.zone
}
