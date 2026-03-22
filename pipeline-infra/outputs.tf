output "api_endpoint" {
  description = "API Gateway endpoint"
  value = "${aws_apigatewayv2_api.log_api.api_endpoint}/logs"
}