resource "aws_ssm_document" "tlz-account-baseline-automation" {
  name          = "tlz-avm-ssm-document"
  document_type = "Automation"

  content = "${file("${path.module}/resources/ssm-master-automation.json")}"
  tags    = "${local.tags}"
}

resource "aws_ssm_document" "tlz-avm-app-automation" {
  name          = "tlz-avm-app-ssm-document"
  document_type = "Automation"

  content = "${file("${path.module}/resources/ssm-master-automation-app.json")}"
  tags    = "${local.tags}"
}

resource "aws_ssm_document" "tlz-avm-non-app-automation" {
  name          = "tlz-avm-non-app-ssm-document"
  document_type = "Automation"

  content = "${file("${path.module}/resources/ssm-master-automation-non-app.json")}"
  tags    = "${local.tags}"
}

resource "aws_ssm_document" "tlz-avm-core-automation" {
  name          = "tlz-avm-core-ssm-document"
  document_type = "Automation"

  content = "${file("${path.module}/resources/ssm-master-automation-core.json")}"
  tags    = "${local.tags}"
}
