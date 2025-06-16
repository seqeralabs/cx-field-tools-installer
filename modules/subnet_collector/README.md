# Subnet Collector Module

## Version
Current version: 1.0.0

## Description
This module centralizes the generation of the hashmap linking subnet CIDR to subnet ID hashmap.
Example { '10.0.1.0/24 => "subnet-12344" }

## Usage
```hcl
module "connection_strings" {
  source = "./modules/subnet_collector/v1.0.0"
  # ... configuration ...
}
```

## Inputs
[Document all input variables]  TODO (via AI)

## Outputs
[Document all outputs]          TODO (via AI)