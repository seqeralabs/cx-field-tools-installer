# I"M NOT CONVINCED THIS MAKES SENSE.

# Global variables. Cant use tfvars values.
variables {
  # bucket_prefix = "test"
  # vpc_existing_id = var.vpc_existing_id   # Error 'Variables may not be used here.'
}


run "01_example_check_vpc_cidr" {

  variables {
    vpc_existing_id = var.vpc_existing_id
  }

  command = plan

  assert {
    # condition     = aws_s3_bucket.bucket.bucket == "test-bucket"
    # error_message = "S3 bucket name did not match expected"
    condition       =  data.aws_vpc.preexisting.cidr_block == "10.2.0.0/16"
    error_message   = "Pre-existing VPC does not have CIDR block '10.2.0.0/16'."
  }

}


# The module does not have an output value for Visibility so I think this sort of test would need to be
# run in the Pytest section. 
run "02_alb_visibility_public_01" {

  variables {
    flag_create_load_balancer = true
    flag_make_instance_public = true
    flag_make_instance_private_behind_public_alb = false
  }

  command = plan

  assert {
    condition       = module.alb[0].internal == false
    error_message   = "ALB should not be Internal-type." 
    }
}