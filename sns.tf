resource "aws_sns_topic" "tlz-avm-notifications" {
  name = "tlz-avm-notifications-${data.aws_caller_identity.current.account_id}"
  tags = "${local.tags}"
}

resource "aws_dynamodb_table_item" "tlz-avm-notifications-topic" {
  table_name = "${aws_dynamodb_table.tlz-avm-config.name}"
  hash_key   = "${aws_dynamodb_table.tlz-avm-config.hash_key}"

  item = <<ITEM
{
  "parameter": {"S": "sns_topic_arn"},
  "value": {"S": "${aws_sns_topic.tlz-avm-notifications.arn}"}
}
ITEM
}
