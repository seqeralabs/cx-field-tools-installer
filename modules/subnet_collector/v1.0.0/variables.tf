variable "create_new_vpc" {
  description = "Whether to create a new VPC or use an existing one"
  type        = bool
}

variable "vpc_id" {
  description = "ID of the existing VPC (required when create_new_vpc is false)"
  type        = string
  default     = null
}

variable "vpc_module" {
  description = "VPC module output (required when create_new_vpc is true)"
  type        = any
  default     = null
}
