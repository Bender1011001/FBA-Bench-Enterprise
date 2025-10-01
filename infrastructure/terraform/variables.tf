variable "domain_name" {
  description = "The domain name for the application"
  type        = string
  default     = "example.com"
}

variable "environment" {
  description = "The deployment environment"
  type        = string
  default     = "sandbox"
}

variable "api_image_tag" {
  description = "The Docker image tag for the API"
  type        = string
  default     = "latest"
}

variable "web_image_tag" {
  description = "The Docker image tag for the web frontend"
  type        = string
  default     = "latest"
}

variable "api_public_base_url" {
  description = "The base URL for the API"
  type        = string
  default     = "http://localhost:8000"
}

variable "frontend_base_url" {
  description = "The base URL for the frontend"
  type        = string
  default     = "http://localhost:5173"
}

variable "stripe_public_key" {
  description = "The Stripe public key"
  type        = string
  default     = "pk_test_CHANGE_ME"
}

variable "stripe_price_id_default" {
  description = "The default Stripe price ID"
  type        = string
  default     = "price_123CHANGE_ME"
}

variable "jwt_secret" {
  description = "The JWT secret key (sensitive)"
  type        = string
  sensitive   = true
  default     = "CHANGE_ME_DEV"
}