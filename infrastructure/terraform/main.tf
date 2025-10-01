resource "random_id" "tenant_suffix" {
  byte_length = 4
}

resource "null_resource" "sandbox_summary" {
  triggers = {
    environment             = var.environment
    domain_name             = var.domain_name
    api_image_tag           = var.api_image_tag
    web_image_tag           = var.web_image_tag
    api_public_base_url     = var.api_public_base_url
    frontend_base_url       = var.frontend_base_url
    stripe_public_key       = var.stripe_public_key
    stripe_price_id_default = var.stripe_price_id_default
    tenant_suffix           = random_id.tenant_suffix.hex
  }
}

# Example of local_file usage (commented out to avoid writing files)
# data "local_file" "example" {
#   filename = "${path.module}/example.txt"
# }