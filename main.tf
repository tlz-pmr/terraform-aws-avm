# AWS provider and region

data "aws_caller_identity" "current" {}

locals {
  baseline_version = "v0.1.13"
  tags = "${module.label.tags}"
}

module "null_label" {
  source = "cloudposse/label/null"
  version = "0.10.0"
  name   = "TLZ_DynamoDB"

  tags = {
    "project"                   = "TLZ"
    "security:data_sensitivity" = "Confidential"
    "stack:region"              = "AMR"
    "stack"                     = "TLZ"
    "stack:version"             = "0.1.0"
    "stack:env:chg_control"     = "true"
    "stack:lifecycle"           = "perm"
    "stack:builder"             = "terraform"
    "stack:env"                 = "Dev"
    "stack:owner"               = "CAP"
    "stack:support_group"       = "blizzard-cloud"
  }
}
