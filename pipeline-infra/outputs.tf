output "api_endpoint" {
  description = "API Gateway endpoint"
  value       = "${aws_apigatewayv2_api.log_api.api_endpoint}/logs"
}

output "sqs_queue_url" {
  description = "SQS queue URL used by producer"
  value       = aws_sqs_queue.logs.url
}

output "consumer_lambda_name" {
  description = "Consumer Lambda function name"
  value       = aws_lambda_function.log_consumer.function_name
}

output "raw_logs_bucket_name" {
  description = "S3 bucket for raw log archival"
  value       = aws_s3_bucket.raw_logs.bucket
}

output "log_metrics_table_name" {
  description = "DynamoDB table for pre-aggregated log metrics"
  value       = aws_dynamodb_table.log_metrics.name
}