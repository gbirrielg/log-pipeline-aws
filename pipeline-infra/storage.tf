# Setting up S3 bucket for raw log storage & configs
resource "aws_s3_bucket" "raw_logs" {
  bucket = "log-pipeline-raw-logs"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_logs_encryption" {
  bucket = aws_s3_bucket.raw_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "raw_logs_public_block" {
  bucket = aws_s3_bucket.raw_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# DynamoDB table for pre-aggregated log metrics per service and time window
resource "aws_dynamodb_table" "log_metrics" {
  name         = "log_metrics"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "service_id"
  range_key    = "sk"

  attribute {
    name = "service_id"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}
