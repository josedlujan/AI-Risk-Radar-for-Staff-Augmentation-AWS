#!/bin/bash
set -e

# Team Risk Analysis System - Local Testing Script
# This script runs the Lambda functions locally using SAM CLI

echo "=========================================="
echo "Team Risk Analysis System - Local Testing"
echo "=========================================="
echo ""

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "Error: SAM CLI is not installed. Please install it first."
    exit 1
fi

# Build the SAM application
echo "Building SAM application..."
sam build

if [ $? -ne 0 ]; then
    echo "Error: SAM build failed"
    exit 1
fi

echo ""
echo "Build completed successfully!"
echo ""

# Start local API
echo "Starting local API Gateway..."
echo "API will be available at: http://127.0.0.1:3000"
echo ""
echo "Available endpoints:"
echo "  POST http://127.0.0.1:3000/api/signals   - Ingest team signals"
echo "  POST http://127.0.0.1:3000/api/analyze   - Trigger analysis"
echo "  GET  http://127.0.0.1:3000/api/risks     - Query risk data"
echo ""
echo "Press Ctrl+C to stop the local API"
echo ""

sam local start-api --port 3000
