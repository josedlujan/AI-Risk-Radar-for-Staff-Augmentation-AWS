#!/bin/bash
set -e

# Team Risk Analysis System - Cleanup Script
# This script removes all AWS resources created by the SAM deployment

echo "=========================================="
echo "Team Risk Analysis System - Cleanup"
echo "=========================================="
echo ""

# Get deployment environment (default to 'dev')
ENVIRONMENT=${1:-dev}
STACK_NAME="team-risk-analysis-$ENVIRONMENT"

echo "WARNING: This will delete all resources in stack: $STACK_NAME"
echo "This includes:"
echo "  - Lambda functions"
echo "  - DynamoDB tables (and all data)"
echo "  - S3 bucket (and all snapshots)"
echo "  - API Gateway"
echo "  - CloudWatch logs and alarms"
echo ""

read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Deleting stack: $STACK_NAME"
echo ""

# Empty S3 bucket first (required before stack deletion)
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`SnapshotsBucketName`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$BUCKET_NAME" ]; then
    echo "Emptying S3 bucket: $BUCKET_NAME"
    aws s3 rm s3://$BUCKET_NAME --recursive --region us-east-1 || true
    echo "✓ S3 bucket emptied"
    echo ""
fi

# Delete the CloudFormation stack
aws cloudformation delete-stack \
    --stack-name $STACK_NAME \
    --region us-east-1

echo "Waiting for stack deletion to complete..."
aws cloudformation wait stack-delete-complete \
    --stack-name $STACK_NAME \
    --region us-east-1

echo ""
echo "=========================================="
echo "Cleanup completed successfully!"
echo "=========================================="
echo ""
