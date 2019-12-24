########################
# IAM Roles for lambda #
########################

resource "aws_iam_role" "iam_role_for_lambda" {
  name = "avm_tfe_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  tags = "${local.tags}"
}

resource "aws_iam_role_policy" "tlz_iam_update_policy" {
  name = "tlz_iam_update_policy"
  role = "${aws_iam_role.iam_role_for_lambda.name}"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "iam:UpdateAssumeRolePolicy",
                "iam:CreatePolicyVersion",
                "iam:DeletePolicyVersion",
                "iam:SetDefaultPolicyVersion"
            ],
            "Resource": [
                "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/tlz_accounts_assumerole_policy",
                "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/avm_tfe_role"
            ]
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": "iam:DeleteAccountPasswordPolicy",
            "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "SecretsManagerReadWrite-attach" {
  role       = "${aws_iam_role.iam_role_for_lambda.name}"
  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
}

resource "aws_iam_role_policy_attachment" "AWSLambdaFullAccess-attach" {
  role       = "${aws_iam_role.iam_role_for_lambda.name}"
  policy_arn = "arn:aws:iam::aws:policy/AWSLambdaFullAccess"
}

resource "aws_iam_role_policy_attachment" "AWSLambdaDynamoDBExecutionRole-attach" {
  role       = "${aws_iam_role.iam_role_for_lambda.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaDynamoDBExecutionRole"
}

resource "aws_iam_role_policy_attachment" "AmazonSSMAutomationRole-attach" {
  role       = "${aws_iam_role.iam_role_for_lambda.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonSSMAutomationRole"
}

resource "aws_iam_role_policy_attachment" "AWSLambdaVPCAccessExecutionRole-attach" {
  role       = "${aws_iam_role.iam_role_for_lambda.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "AmazonSESFullAccess-attach" {
  role       = "${aws_iam_role.iam_role_for_lambda.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonSESFullAccess"
}

resource "aws_iam_role_policy_attachment" "accounts-assumeRole-policy-attach" {
  role       = "${aws_iam_role.iam_role_for_lambda.name}"
  policy_arn = "${aws_iam_policy.tlz_accounts_assumerole_policy.arn}"
}

# resource "aws_iam_role_policy_attachment" "accounts-assumeRole-policy-update-attach" {
#   role       = "${aws_iam_role.iam_role_for_lambda.name}"
#   policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/tlz_iam_update_policy"
# }

# resource "aws_iam_role_policy_attachment" "accountbaseline-resources-policy-attach" {
#   role       = "${aws_iam_role.iam_role_for_lambda.name}"
#   policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/TLZ_AWS_AccountBaseline_Resources_Policy"
# }

##################################
# tlz_accounts_assumerole_policy #
##################################

resource "aws_iam_policy" "tlz_accounts_assumerole_policy" {
  name   = "tlz_accounts_assumerole_policy"
  policy = "${data.aws_iam_policy_document.tlz_accounts_assumerole_policy.json}"

  # This policy is going to eventually be managed by lambdas. Terraform will only instantiate.
  lifecycle {
    ignore_changes = ["policy"]
  }
}

data "aws_iam_policy_document" "tlz_accounts_assumerole_policy" {
  statement {
    sid     = "0"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    resources = [
      "arn:aws:iam::${var.master_payer_account}:role/${var.tlz_org_account_access_role}",
      "arn:aws:iam::${var.master_payer_account}:role/${var.tlz_admin_role}",
      "arn:aws:iam::${var.core_logging_account}:role/${var.tlz_admin_role}",
      "arn:aws:iam::${var.core_security_account}:role/${var.tlz_admin_role}"
    ]
  }
}
