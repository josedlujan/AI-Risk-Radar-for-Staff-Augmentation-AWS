#!/bin/bash
set -e

# Team Risk Analysis System - Template Validation Script
# This script validates the SAM template and checks for common issues

echo "=========================================="
echo "Team Risk Analysis System - Validation"
echo "=========================================="
echo ""

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "Error: SAM CLI is not installed. Please install it first."
    exit 1
fi

# Validate SAM template
echo "Validating SAM template..."
sam validate --lint

if [ $? -ne 0 ]; then
    echo "Error: SAM template validation failed"
    exit 1
fi

echo ""
echo "✓ SAM template is valid"
echo ""

# Check if required files exist
echo "Checking required files..."

REQUIRED_FILES=(
    "backend/lambdas/ingest/handler.py"
    "backend/lambdas/ingest/requirements.txt"
    "backend/lambdas/analyze/handler.py"
    "backend/lambdas/analyze/requirements.txt"
    "backend/lambdas/query/handler.py"
    "backend/lambdas/query/requirements.txt"
    "backend/requirements.txt"
)

ALL_FILES_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "✗ Missing: $file"
        ALL_FILES_EXIST=false
    else
        echo "✓ Found: $file"
    fi
done

echo ""

if [ "$ALL_FILES_EXIST" = false ]; then
    echo "Error: Some required files are missing"
    exit 1
fi

echo "✓ All required files exist"
echo ""

# Check Python syntax
echo "Checking Python syntax..."
python3 -m py_compile backend/lambdas/ingest/handler.py
python3 -m py_compile backend/lambdas/analyze/handler.py
python3 -m py_compile backend/lambdas/query/handler.py

if [ $? -ne 0 ]; then
    echo "Error: Python syntax check failed"
    exit 1
fi

echo "✓ Python syntax is valid"
echo ""

echo "=========================================="
echo "Validation completed successfully!"
echo "=========================================="
echo ""
