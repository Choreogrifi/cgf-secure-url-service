#!/bin/bash -eu

set -e

# Set the project ID
PROJECT_ID=$(gcloud config get-value project)

# Set the region
REGION=$(gcloud config get-value compute/region)

# Set the service name
SERVICE_NAME="file-downloader-api"

# Set the service account name that has permission to invoke the Cloud Run servicesoure
#SERVICE_ACCOUNT="sa-cr-payment@grpit-cds-sandpit-dev.iam.gserviceaccount.com" 

# Use Cloud Build to build the image
gcloud builds submit --tag europe-west1-docker.pkg.dev/$PROJECT_ID/cloudrun/$SERVICE_NAME  --timeout 120s

# Set the image name
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/cloudrun/$SERVICE_NAME"

# Set the location
LOCATION="europe-west1"

# Deploy the service
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --region $REGION \
  --allow-unauthenticated \
  --timeout 120s \
  --memory 256M \
  --concurrency 80 \
  --max-instances 10 \
  --min-instances 0 \
  --ingress=all \
  --service-account=sa-abacus-signed-url \
  --set-env-vars ENVIRONMENT=development,GCP_PROJECT=$PROJECT_ID

  SERVICE_URL=$( \
  gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format "value(status.url)" \
)

echo $SERVICE_URL