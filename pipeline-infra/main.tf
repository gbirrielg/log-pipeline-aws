# Setting up Lambda execution role with necessary permissions
resource "aws_iam_role" "lambda_role" {
  name = "log-pipeline-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy" "producer_sqs_send" {
  name = "log-producer-sqs-send"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = aws_sqs_queue.logs.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "consumer_storage_access" {
  name = "log-consumer-storage-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.raw_logs.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "consumer_dynamodb_access" {
  name = "log-consumer-dynamodb-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:UpdateItem"]
        Resource = aws_dynamodb_table.log_metrics.arn
      }
    ]
  })
}


# Producer Lambda function packaging and deployment
data "archive_file" "producer_lambda_zip" {
  type        = "zip"
  source_file = "lambda/producer.py"
  output_path = "lambda/producer.zip"
}

resource "aws_lambda_function" "log_producer" {
  filename         = data.archive_file.producer_lambda_zip.output_path
  function_name    = "log-producer"
  role             = aws_iam_role.lambda_role.arn
  handler          = "producer.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.producer_lambda_zip.output_base64sha256

  environment {
    variables = {
      QUEUE_URL = aws_sqs_queue.logs.url
    }
  }
}


# Consumer Lambda function packaging and deployment
data "archive_file" "consumer_lambda_zip" {
  type        = "zip"
  source_file = "lambda/consumer.py"
  output_path = "lambda/consumer.zip"
}

resource "aws_lambda_function" "log_consumer" {
  filename         = data.archive_file.consumer_lambda_zip.output_path
  function_name    = "log-consumer"
  role             = aws_iam_role.lambda_role.arn
  handler          = "consumer.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.consumer_lambda_zip.output_base64sha256

  environment {
    variables = {
      RAW_LOGS_BUCKET = aws_s3_bucket.raw_logs.bucket
      METRICS_TABLE   = aws_dynamodb_table.log_metrics.name
    }
  }
}


# AWS API Gateway v2 configuration
resource "aws_apigatewayv2_api" "log_api" {
  name          = "log-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.log_api.id
  name        = "$default"
  auto_deploy = true
}


# AWS Lambda integration with API Gateway
resource "aws_apigatewayv2_integration" "producer_lambda" {
  api_id                 = aws_apigatewayv2_api.log_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.log_producer.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "logs" {
  api_id    = aws_apigatewayv2_api.log_api.id
  route_key = "POST /logs"
  target    = "integrations/${aws_apigatewayv2_integration.producer_lambda.id}"
}

resource "aws_lambda_permission" "api_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.log_producer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.log_api.execution_arn}/*/*"
}
