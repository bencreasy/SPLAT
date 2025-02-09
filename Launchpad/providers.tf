### providers.tf
```hcl
provider "google" {
  project = var.splat_launchpad
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}
```
