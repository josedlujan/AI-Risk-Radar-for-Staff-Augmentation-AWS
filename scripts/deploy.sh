#!/bin/bash
set -e

# Team Risk Analysis System - Deployment Script
# This script builds and deploys the SAM application to AWS

echo "=========================================="
echo "Team Risk Analysis System - Deployment"
echo "=========================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "Error: SAM CLI is not installed. Please install it first."
    exit 1
fi

# Get deployment environment (default to 'dev')
ENVIRONMENT=${1:-dev}
echo "Deploying to environment: $ENVIRONMENT"
echo ""

# Build the SAM application
echo "Building SAM application..."
sam build --use-container

if [ $? -ne 0 ]; then
    echo "Error: SAM build failed"
    exit 1
fi

echo ""
echo "Build completed successfully!"
echo ""

# Deploy the SAM application
echo "Deploying SAM application..."
if [ "$ENVIRONMENT" == "prod" ]; then
    # Production deployment with confirmation
    sam deploy \
        --stack-name team-risk-analysis-prod \
        --capabilities CAPABILITY_IAM \
        --region us-east-1 \
        --no-fail-on-empty-changeset \
        --confirm-changeset
else
    # Development deployment without confirmation
    sam deploy \
        --stack-name team-risk-analysis-dev \
        --capabilities CAPABILITY_IAM \
        --region us-east-1 \
        --no-fail-on-empty-changeset \
        --no-confirm-changeset
fi

if [ $? -ne 0 ]; then
    echo "Error: SAM deployment failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
echo ""

# Get stack outputs
echo "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name team-risk-analysis-$ENVIRONMENT \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo ""
echo "To test the API, use the ApiEndpoint URL shown above."
echo ""
