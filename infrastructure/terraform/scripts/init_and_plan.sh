#!/bin/bash

# Script to initialize and plan the Terraform managed sandbox deployment
# Run from the infrastructure/terraform directory after copying tfvars if needed

set -e  # Exit on any error

echo "Copying dev.tfvars.example to dev.tfvars..."
cp env/dev.tfvars.example env/dev.tfvars

echo "Running terraform init..."
terraform init

echo "Running terraform plan..."
terraform plan -var-file=env/dev.tfvars