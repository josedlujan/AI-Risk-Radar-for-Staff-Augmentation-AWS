#!/bin/bash
set -e

# Team Risk Analysis System - CloudWatch Dashboard Setup
# This script creates a CloudWatch dashboard for monitoring

echo "=========================================="
echo "CloudWatch Dashboard Setup"
echo "=========================================="
echo ""

# Get deployment environment (default to 'dev')
ENVIRONMENT=${1:-dev}
DASHBOARD_NAME="TeamRiskAnalysis-$ENVIRONMENT"

echo "Creating CloudWatch dashboard: $DASHBOARD_NAME"
echo ""

# Create the dashboard
aws cloudwatch put-dashboard \
    --dashboard-name "$DASHBOARD_NAME" \
    --dashboard-body file://cloudwatch-dashboard.json \
    --region us-east-1

if [ $? -ne 0 ]; then
    echo "Error: Failed to create CloudWatch dashboard"
    exit 1
fi

echo ""
echo "✓ CloudWatch dashboard created successfully!"
echo ""
echo "View the dashboard at:"
echo "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=$DASHBOARD_NAME"
echo ""
