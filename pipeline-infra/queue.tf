resource "aws_sqs_queue" "logs" {
	name = "log-pipeline-logs"
}

resource "aws_lambda_event_source_mapping" "consumer_sqs_mapping" {
	event_source_arn                   = aws_sqs_queue.logs.arn
	function_name                      = aws_lambda_function.log_consumer.arn
	batch_size                         = 25
	maximum_batching_window_in_seconds = 20
}
