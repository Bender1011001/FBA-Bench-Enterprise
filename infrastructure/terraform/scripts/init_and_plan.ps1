# PowerShell script to initialize and plan the Terraform managed sandbox deployment
# Run from the infrastructure/terraform directory after copying tfvars if needed

Write-Host "Copying dev.tfvars.example to dev.tfvars..."
Copy-Item env/dev.tfvars.example env/dev.tfvars

Write-Host "Running terraform init..."
terraform init

Write-Host "Running terraform plan..."
terraform plan -var-file=env/dev.tfvars