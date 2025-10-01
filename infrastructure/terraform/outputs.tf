output "sandbox_summary" {
  description = "Structured summary of sandbox configuration and computed values"
  value = {
    tenant_suffix      = random_id.tenant_suffix.hex
    environment        = var.environment
    domain_name        = var.domain_name
    api_image_tag      = var.api_image_tag
    web_image_tag      = var.web_image_tag
    api_base_url       = var.api_public_base_url
    frontend_base_url  = var.frontend_base_url
    stripe_public_key  = var.stripe_public_key
    stripe_price_id    = var.stripe_price_id_default
  }
}