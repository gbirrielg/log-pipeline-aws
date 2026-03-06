set -e

echo "Destroying pipeline-infra..."
cd pipeline-infra
terraform destroy

cd ..
echo "Destroying backend-bootstrap..."
cd backend-bootstrap
terraform destroy -var-file=bootstrap.tfvars
cd ..

echo "All resources destroyed successfully."