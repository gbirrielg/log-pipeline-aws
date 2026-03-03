variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "The AWS CLI profile to use for authentication."
  type        = string
  default     = "default"
}

variable "state_bucket_name" {
  description = "The name of the S3 bucket to store Terraform state files."
  type        = string
}

variable "lock_table_name" {
  description = "The name of the DynamoDB table to use for Terraform state locking."
  type        = string
  default = "terraform-state-lock"
}