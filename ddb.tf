# Table that stores the AWS account and organizational unit information
resource "aws_dynamodb_table" "org-details" {
  name           = "OrgDetails"
  read_capacity  = 1
  write_capacity = 1
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "type"
    type = "S"
  }

  attribute {
    name = "parent_id"
    type = "S"
  }

  global_secondary_index {
    name            = "parentIndex"
    hash_key        = "parent_id"
    write_capacity  = 1
    read_capacity   = 1
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "typeIndex"
    hash_key        = "type"
    write_capacity  = 1
    read_capacity   = 1
    projection_type = "ALL"
  }

  tags = "${module.label.tags}"
}

# Table that stores the configuration details for the account vending machine
resource "aws_dynamodb_table" "tlz-avm-config" {
  name           = "AVMConfig"
  read_capacity  = 1
  write_capacity = 1
  hash_key       = "parameter"

  attribute {
    name = "parameter"
    type = "S"
  }

  tags = "${module.label.tags}"
}

# Table that stores the configuration details for the account vending machine
resource "aws_dynamodb_table" "org-account-request" {
  name             = "OrgAccountRequest"
  read_capacity    = 1
  write_capacity   = 1
  hash_key         = "id"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "id"
    type = "S"
  }

  tags = "${module.label.tags}"
}

# DynamoDB trigger Lambda function

resource "aws_lambda_event_source_mapping" "db_lambda_trigger" {
  depends_on        = ["aws_dynamodb_table.org-account-request"]
  event_source_arn  = "${aws_dynamodb_table.org-account-request.stream_arn}"
  function_name     = "${aws_lambda_function.master_respond-to-accountcreation.arn}"
  starting_position = "LATEST"
  batch_size        = 1
}

# variable "master_payer_account" {
#   description = "AccountID of master_payer account"
# }

# variable "core_logging_account" {
#   description = "AccountID of core-logging account"
# }

# variable "core_security_account" {
#   description = "AccountID of core_security account"
# }

# variable "core_shared_services_account" {
#   description = "AccountID of shared-services account"
# }
resource "aws_dynamodb_table_item" "tlz-master_payer_account" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "master_payer_account"},
  "value": {"S": "${var.master_payer_account}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tlz-core_logging_account" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "core_logging_account"},
  "value": {"S": "${var.core_logging_account}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tlz-core_security_account" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "core_security_account"},
  "value": {"S": "${var.core_security_account}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tlz-core_shared_services_account" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "core_shared_services_account"},
  "value": {"S": "${var.core_shared_services_account}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tlz-admin-role-item" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "tlz_admin_role"},
  "value": {"S": "${var.tlz_admin_role}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tlz-avm_activity_sns_subscribers" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "avm_activity_sns_subscribers"},
  "value": {"S": "${var.avm_activity_sns_subscribers}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tlz-post_account_sender_email" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "post_account_sender_email"},
  "value": {"S": "${var.post_account_sender_email}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tlz-post_account_subscriber_emails" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "post_account_subscriber_emails"},
  "value": {"S": "${var.post_account_subscriber_emails}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tlz_git_url" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "tlz_git_url"},
  "value": {"S": "${var.tlz_git_url}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "avm_workspace_name" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "avm_workspace_name"},
  "value": {"S": "${var.avm_workspace_name}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "logging_workspace_name" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "logging_workspace_name"},
  "value": {"S": "${var.logging_workspace_name}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "master_payer_org_id" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "master_payer_org_id"},
  "value": {"S": "${var.master_payer_org_id}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "primary_zone_name" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "primary_zone_name"},
  "value": {"S": "${var.primary_zone_name}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "project_for_templates" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "project_for_templates"},
  "value": {"S": "${var.project_for_templates}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "secondary_region" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "secondary_region"},
  "value": {"S": "${var.secondary_region}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tags" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "tags"},
  "value": {"S": "{\n    \"project\"     : \"${var.project}\",\n    \"security:data_sensitivity\" : \"${var.security-data_sensitivity}\",\n    \"stack:region\" : \"${var.stack-region}\",\n        \"stack\" : \"${var.stack}\",\n    \"stack:version\" : \"${var.stack-version}\",\n    \"stack:env:chg_control\" : \"${var.stack-env-chg_control}\",\n    \"stack:lifecycle\" : \"${var.stack-lifecycle}\",\n    \"stack:builder\" : \"${var.stack-builder}\",\n    \"stack:env\" : \"${var.stack-env}\",\n    \"stack:owner\" : \"${var.stack-owner}\",\n    \"stack:support_group\" :     \"${var.stack-support_group}\"\n  }"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tfe_api_url" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "tfe_api_url"},
  "value": {"S": "${var.tfe_api_url}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tfe_org_name" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "tfe_org_name"},
  "value": {"S": "${var.tfe_org_name}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "tlz_org_account_access_role" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "tlz_org_account_access_role"},
  "value": {"S": "${var.tlz_org_account_access_role}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "vended_applications_project" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "vended_applications_project"},
  "value": {"S": "${var.vended_applications_project}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "vended_baselines_project" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "vended_baselines_project"},
  "value": {"S": "${var.vended_baselines_project}"}
}
ITEM
}

resource "aws_dynamodb_table_item" "terraform_service_user" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "terraform_service_user"},
  "value": {"S": "${var.terraform_service_user}"}
}
ITEM
}

module "label" {
  source = "git::https://github.com/cloudposse/terraform-null-label.git?ref=tags/0.11.1"
  name   = "TLZ_DynamoDB"

  tags = {
    "project"                   = "${var.project}"
    "security:data_sensitivity" = "${var.security-data_sensitivity}"
    "stack:region"              = "${var.stack-region}"
    "stack"                     = "${var.stack}"
    "stack:version"             = "${var.stack-version}"
    "stack:env:chg_control"     = "${var.stack-env-chg_control}"
    "stack:lifecycle"           = "${var.stack-lifecycle}"
    "stack:builder"             = "${var.stack-builder}"
    "stack:env"                 = "${var.stack-env}"
    "stack:owner"               = "${var.stack-owner}"
    "stack:support_group"       = "${var.stack-support_group}"
  }
}
