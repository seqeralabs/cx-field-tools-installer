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

variable "subnets_ec2" {
  description = "List of EC2 subnets"
  type        = list(string)
}

variable "subnets_batch" {
  description = "List of Batch subnets"
  type        = list(string)
}

variable "subnets_db" {
  description = "List of DB subnets"
  type        = list(string)
}

variable "subnets_redis" {
  description = "List of Redis subnets"
  type        = list(string)
}

variable "subnets_alb" {
  description = "List of ALB subnets"
  type        = list(string)
}


## ------------------------------------------------------------------------------------
## Testing
## ------------------------------------------------------------------------------------
variable "local_testing_active" {
  type        = bool
  default     = false
  description = "Use to drive mocking behaviour for to-be-created resources."
}
