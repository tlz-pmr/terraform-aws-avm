# Master lambda
data "archive_file" "avm-master" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-master/"
  output_path = "${path.module}/lambda/avm-master.zip"
}

resource "aws_lambda_function" "master_respond-to-accountcreation" {
  function_name    = "avm-master-respond-to-account-creation"
  description      = "Lambda to create/validate aws account from webform input or OrgAccountRequest DB entry insert"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-master.lambda_handler"
  filename         = "${path.module}/lambda/avm-master.zip"
  source_code_hash = "${data.archive_file.avm-master.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}

# Delete default vpc
data "archive_file" "avm-deletevpc" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-vpc-defaultdelete/"
  output_path = "${path.module}/lambda/avm-vpc-defaultdelete.zip"
}

resource "aws_lambda_function" "avm-deletevpc" {
  function_name    = "avm-vpcs-delete-defaults"
  description      = "Lambda to remove default vpcs"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-vpc-defaultdelete.lambda_handler"
  filename         = "${path.module}/lambda/avm-vpc-defaultdelete.zip"
  source_code_hash = "${data.archive_file.avm-deletevpc.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}

# IAM Managed policy update
data "archive_file" "avm-iamupdate" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-iam-updatepolicy/"
  output_path = "${path.module}/lambda/avm-iam-updatepolicy.zip"
}

resource "aws_lambda_function" "avm-iam-updatepolicy" {
  function_name    = "avm-iam-managedpolicy-update-for-new-account"
  description      = "Lambda to update managed policy to include new account"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-iam-updatepolicy.lambda_handler"
  filename         = "${path.module}/lambda/avm-iam-updatepolicy.zip"
  source_code_hash = "${data.archive_file.avm-iamupdate.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}

# # redlock account add lambda
data "archive_file" "avm_redlock" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-redlock-invites/"
  output_path = "${path.module}/lambda/avm-redlock-invites.zip"
}

resource "aws_lambda_function" "redlock-addaccount" {
  function_name    = "avm-3rdparty-redlock-addaccount"
  description      = "Lambda to register new account with redlock"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-redlock-invites.lambda_handler"
  filename         = "${path.module}/lambda/avm-redlock-invites.zip"
  source_code_hash = "${data.archive_file.avm_redlock.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}

# Guardduty Invite lambda
data "archive_file" "avm-guardduty" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-guardduty-invites/"
  output_path = "${path.module}/lambda/avm-guardduty-invites.zip"
}

resource "aws_lambda_function" "avm-guardduty-invites" {
  function_name    = "avm-guardduty-invite-member-accounts"
  description      = "Lambda to send invite member accounts from master GD Account and Accept"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-guardduty-invites.lambda_handler"
  filename         = "${path.module}/lambda/avm-guardduty-invites.zip"
  source_code_hash = "${data.archive_file.avm-guardduty.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}

# CW destination policy update lambda
data "archive_file" "avm-cwpolicy" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-cwpolicy-update/"
  output_path = "${path.module}/lambda/avm-cwpolicy-update.zip"
}

resource "aws_lambda_function" "avm-cwpolicy-update" {
  function_name    = "avm-update-cw-destination-policy"
  description      = "Lambda to update CW destination policy"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-cwpolicy-update.lambda_handler"
  filename         = "${path.module}/lambda/avm-cwpolicy-update.zip"
  source_code_hash = "${data.archive_file.avm-cwpolicy.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}

# Okta Create groups
data "archive_file" "avm-oktagroups" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-okta-groups/"
  output_path = "${path.module}/lambda/avm-okta-groups.zip"
}

resource "aws_lambda_function" "avm-okta-groups" {
  function_name    = "avm-okta-create-groups"
  description      = "Lambda to create Okta groups"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-okta-groups.lambda_handler"
  filename         = "${path.module}/lambda/avm-okta-groups.zip"
  source_code_hash = "${data.archive_file.avm-oktagroups.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}

# S3 Bucket policy update
data "archive_file" "avm-s3policyupdate" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-s3-updatepolicy/"
  output_path = "${path.module}/lambda/avm-s3-updatepolicy.zip"
}

resource "aws_lambda_function" "avm-s3-updatepolicy" {
  function_name    = "avm-s3-update-corelogging-bucket-policies"
  description      = "Lambda to Update AWS Config and cloudtrail S3 bucket policies"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-s3-updatepolicy.lambda_handler"
  filename         = "${path.module}/lambda/avm-s3-updatepolicy.zip"
  source_code_hash = "${data.archive_file.avm-s3policyupdate.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}

# SNS Post account creation lambda
data "archive_file" "avm-snspostaccount" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-sns-postaccount/"
  output_path = "${path.module}/lambda/avm-sns-postaccount.zip"
}

resource "aws_lambda_function" "avm-sns-postaccount" {
  function_name    = "avm-sns-post-account-creation-email"
  description      = "Lambda to send sns email post account creation"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-sns-postaccount.lambda_handler"
  filename         = "${path.module}/lambda/avm-sns-postaccount.zip"
  source_code_hash = "${data.archive_file.avm-snspostaccount.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}

# # SNS Post account creation lambda
data "archive_file" "avm-ssmvalidate" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-ssm-validate/"
  output_path = "${path.module}/lambda/avm-ssm-validate.zip"
}

resource "aws_lambda_function" "avm-ssm-validate" {
  function_name    = "avm-ssm-validate-doc-status"
  description      = "Lambda to validate the SSM automation status of previous steps"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-ssm-validate.lambda_handler"
  filename         = "${path.module}/lambda/avm-ssm-validate.zip"
  source_code_hash = "${data.archive_file.avm-ssmvalidate.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}

# # Support email lambda
# data "archive_file" "avm-supportemail" {
#   type        = "zip"
#   source_dir  = "${path.module}/lambda/avm-support-request/"
#   output_path = "${path.module}/lambda/avm-support-request.zip"
# }

# resource "aws_lambda_function" "avm-supportemail" {
#   function_name    = "avm-support-request-enterprise-support-by-email"
#   description      = "Lambda to send email to AWS Support"
#   role             = "${aws_iam_role.iam_role_for_lambda.arn}"
#   memory_size      = "${var.memory_size}"
#   runtime          = "${var.runtime}"
#   timeout          = "${var.timeout}"
#   handler          = "avm-support-request.lambda_handler"
#   filename         = "${path.module}/lambda/avm-support-request.zip"
#   source_code_hash = "${data.archive_file.avm-supportemail.output_base64sha256}"
#   layers = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
# }

# TFE baseline lambda
data "archive_file" "avm-tfe-apply-baseline" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-tfe-apply-baseline/"
  output_path = "${path.module}/lambda/avm-tfe-apply-baseline.zip"
}

resource "aws_lambda_function" "avm-tfebaseline" {
  function_name    = "avm-tfe-createbaseline"
  description      = "Lambda to invoke tfe workspace baseline"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-tfe-apply-baseline.lambda_handler"
  filename         = "${path.module}/lambda/avm-tfe-apply-baseline.zip"
  source_code_hash = "${data.archive_file.avm-tfe-apply-baseline.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]

  vpc_config {
    subnet_ids         = "${var.subnet_ids}"
    security_group_ids = "${var.security_group_ids}"
  }

  tags = "${local.tags}"
}

# TFE baseline lambda
data "archive_file" "avm-tfeworkspace" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-tfe-workspaces/"
  output_path = "${path.module}/lambda/avm-tfe-workspaces.zip"
}

resource "aws_lambda_function" "avm-tfeworkspace" {
  function_name    = "avm-tfe-create-workspaces"
  description      = "Lambda to create TFE Workspaces"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-tfe-workspaces.lambda_handler"
  filename         = "${path.module}/lambda/avm-tfe-workspaces.zip"
  source_code_hash = "${data.archive_file.avm-tfeworkspace.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]

  vpc_config {
    subnet_ids         = "${var.subnet_ids}"
    security_group_ids = "${var.security_group_ids}"
  }

  tags = "${local.tags}"
}

# TFE key rotation
data "archive_file" "avm-tfekey" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-tfe-secretrotation/"
  output_path = "${path.module}/lambda/avm-tfe-secretrotation.zip"
}

resource "aws_lambda_function" "avm-tfekey" {
  function_name    = "avm-tfe-secret-rotation"
  description      = "Lambda to rotate secret keys in TFE Workspaces"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-tfe-secretrotation.lambda_handler"
  filename         = "${path.module}/lambda/avm-tfe-secretrotation.zip"
  source_code_hash = "${data.archive_file.avm-tfekey.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]

  vpc_config {
    subnet_ids         = "${var.subnet_ids}"
    security_group_ids = "${var.security_group_ids}"
  }

  tags = "${local.tags}"
}

# Create Git repos
data "archive_file" "avm-gitrepocreate" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-create-github-repo/"
  output_path = "${path.module}/lambda/avm-create-github-repo.zip"
}

resource "aws_lambda_function" "avm-gitrepocreate" {
  function_name    = "avm-create-gitrepos"
  description      = "Lambda to create Git repos"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "git-repo-create.lambda_handler"
  filename         = "${path.module}/lambda/avm-create-github-repo.zip"
  source_code_hash = "${data.archive_file.avm-gitrepocreate.output_base64sha256}"

  vpc_config {
    subnet_ids         = "${var.subnet_ids}"
    security_group_ids = "${var.security_group_ids}"
  }

  layers = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags   = "${local.tags}"
}

data "archive_file" "avm_dns" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/avm-dns-invites/"
  output_path = "${path.module}/lambda/avm-dns-invites.zip"
}

resource "aws_lambda_function" "dns-invite-member-accounts" {
  function_name    = "avm-dns-invite-member-account-vpcs"
  description      = "Lambda for dns invite - new member account"
  role             = "${aws_iam_role.iam_role_for_lambda.arn}"
  memory_size      = "${var.memory_size}"
  runtime          = "${var.runtime}"
  timeout          = "${var.timeout}"
  handler          = "avm-dns-invites.lambda_handler"
  filename         = "${path.module}/lambda/avm-dns-invites.zip"
  source_code_hash = "${data.archive_file.avm_dns.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.avm-lambda-layer.arn}"]
  tags             = "${local.tags}"
}
