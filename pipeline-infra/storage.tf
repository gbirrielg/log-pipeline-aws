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
