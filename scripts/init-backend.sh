#!/bin/bash

cd backend-bootstrap
terraform apply -var-file=bootstrap.tfvars

BUCKET=$(terraform output -raw state_bucket_name)
TABLE=$(terraform output -raw lock_table_name)

cd ../pipeline-infra
terraform init \
  -backend-config="bucket=$BUCKET" \
  -backend-config="dynamodb_table=$TABLE" \
  -backend-config="region=us-east-1" \
  -backend-config="key=pipeline-infra.tfstate" \
  -backend-config="encrypt=true" \
  -reconfigure

terraform apply