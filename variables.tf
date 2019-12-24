variable "runtime" {
  description = "Runtime of Lambda function"
  default     = "python3.7"
}

variable "timeout" {
  description = "Timeout value for Lambda function"
  default     = 300
}

variable "memory_size" {
  description = "Timeout value for Lambda function"
  default     = 150
}

variable "subnet_ids" {
  type        = "list"
  description = "subnet_ids used by lambdas that call GHE and TFE"
}

variable "master_payer_account" {
  description = "AccountID of master_payer account"
}

variable "core_logging_account" {
  description = "AccountID of core-logging account"
}

variable "core_security_account" {
  description = "AccountID of core_security account"
}

variable "core_shared_services_account" {
  description = "AccountID of shared-services account"
}

variable "tlz_admin_role" {
  description = "Admin role that is used"
}

variable "security_group_ids" {
  type        = "list"
  description = "security_group_ids used by lambdas that call GHE and TFE"
}

variable "avm_activity_sns_subscribers" {
  description = "Emails of avm_activity_sns_subscribers"
}

variable "post_account_sender_email" {
  description = "Email id of post_account_sender_email"
}

variable "post_account_subscriber_emails" {
  description = "Email ids of post_account_subscriber_emails"
}

variable "tlz_git_url" {
  description = "url for bitbucket or github repositores"
}

####################
# dynamodb entries #
####################

variable "avm_workspace_name" {
  type        = "string"
  description = "Name of the PTFE workspace the AVM will be deployed through"
  default     = "AVM"
}

variable "logging_workspace_name" {
  type        = "string"
  description = "Name of the PTFE workspace the Logging account will be deployed through"
  default     = "res-core_logging"
}

variable "master_payer_org_id" {
  type        = "string"
  description = "Organization ID for the organization in the master payer account"
}

variable "project_for_templates" {
  type        = "string"
  description = "Bitbucket project where the account templates can be found"
  default     = "tlz-at"
}

variable "secondary_region" {
  type        = "string"
  description = "Secondary region for accounts that may need it"
}

variable "tfe_api_url" {
  type        = "string"
  description = "URL for the v2 API for PTFE. Should be https://<ptfe_hostname>/api/v2"
}

variable "tfe_org_name" {
  type        = "string"
  description = "Name of the organization the TLZ will be deployed through in PTFE"
}

variable "tlz_org_account_access_role" {
  type        = "string"
  description = "Name of the role created when accounts are created by organizations"
  default     = "tlz_organization_account_access_role"
}

variable "vended_applications_project" {
  type        = "string"
  description = "Bitbucket project where the user-facing repos will be created"
  default     = "tlz-va"
}

variable "vended_baselines_project" {
  type        = "string"
  description = "Bitbucket project where vended baselines will be forked into"
  default     = "tlz-vb"
}

variable "project" {
  type        = "string"
  description = "Project name to tag TLZ resources with"
  default     = "TLZ"
}

variable "security-data_sensitivity" {
  type        = "string"
  description = "Data sensitivity classification to tag TLZ resources with"
  default     = "Confidential"
}

variable "stack-region" {
  type        = "string"
  description = "Region to tag TLZ resources with (AMR/EU/APAC)"
  default     = "AMR"
}

variable "stack" {
  type        = "string"
  description = "Stack name to tag TLZ resources with"
  default     = "TLZ"
}

variable "stack-version" {
  type        = "string"
  description = "TLZ version to tag TLZ resources with"
}

variable "stack-env-chg_control" {
  type        = "string"
  description = "Change control classification to tag TLZ resources with"
  default     = "true"
}

variable "stack-lifecycle" {
  type        = "string"
  description = "Lifecycle classification to tag TLZ resources with"
  default     = "perm"
}

variable "stack-builder" {
  type        = "string"
  description = "Tag value denoting what tool is building TLZ resources"
  default     = "Terraform"
}

variable "stack-env" {
  type        = "string"
  description = "Environment type to tag TLZ resources with"
}

variable "stack-owner" {
  type        = "string"
  description = "Team to tag TLZ resources with to denote support ownership"
}

variable "stack-support_group" {
  type        = "string"
  description = "Email to tag TLZ resources with to direct support requests"
}

variable "primary_zone_name" {
  type        = "string"
  description = "DNS zone name to use for AVM resources. This should be the raw domain name, eg: 'example.com'"
}

variable "terraform_service_user" {
  type        = "string"
  description = "the name of the IAM service user"
}
