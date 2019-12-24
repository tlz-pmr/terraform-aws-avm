data "archive_file" "zipit" {
  type        = "zip"
  source_dir  = "${path.module}/layers"
  output_path = "${path.module}/layers/avm-common-functions-layer.zip"
}

resource "aws_lambda_layer_version" "avm-lambda-layer" {
  filename            = "${path.module}/layers/avm-common-functions-layer.zip"
  layer_name          = "avm-common-functions-layer"
  compatible_runtimes = ["python3.7"]
  source_code_hash    = "${data.archive_file.zipit.output_base64sha256}"
}
