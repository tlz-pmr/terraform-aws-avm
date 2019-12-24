output "iam_role_arn" {
  description = "ARN of admin IAM role"
  value       = "${element(concat(aws_iam_role.iam_role_for_lambda.*.arn, list("")), 0)}"
}

output "baseline_version" {
  description = "Version of the baseline module"
  value       = "${local.baseline_version}"
}

output "avm_config_table_name" {
  description = "Name of avm_config dynamo db table"
  value       = "${aws_dynamodb_table.tlz-avm-config.name}"
}

output "avm_config_table_hash" {
  description = "Hash key of avm_config table"
  value       = "${aws_dynamodb_table.tlz-avm-config.hash_key}"
}