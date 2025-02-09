terraform {
  backend "gcs" {
    bucket = "splat-terraform-state-dev"
    prefix = "terraform/state"

    # Enables bucket versioning for state file protection
    enable_bucket_versioning = true

    # Add encryption key if using customer-managed encryption
    # encryption_key = "" // Optional: CMEK configuration

    # Ensure single-user access to prevent state conflicts
    lock_table = "splat-terraform-locks-dev"
  }
}
