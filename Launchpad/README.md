## Deployment Instructions

```bash
# Initialize Terraform
cd launchpad
terraform init

# Create a new workspace for development
terraform workspace new dev

# Plan the deployment
terraform plan -var-file=environments/dev.tfvars

# Apply the configuration
terraform apply -var-file=environments/dev.tfvars

# For cleanup
terraform destroy -var-file=environments/dev.tfvars
```
