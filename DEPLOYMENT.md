# Deployment Guide

This guide walks you through deploying AI Risk Radar to AWS.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **AWS SAM CLI** installed
4. **Python 3.13** installed
5. **Node.js 18+** installed

## Step 1: Configure AWS Credentials

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (e.g., `json`)

## Step 2: Enable Amazon Bedrock Access

1. Go to AWS Console → Amazon Bedrock
2. Navigate to Model Access
3. Enable access to **Claude Sonnet 4** (Anthropic models)
4. If prompted, submit use case details for first-time access

## Step 3: Deploy Backend

```bash
# Build the SAM application
sam build

# Deploy with guided prompts (first time)
sam deploy --guided
```

During guided deployment, you'll be asked:

- **Stack Name**: `team-risk-analysis` (or your preferred name)
- **AWS Region**: Your preferred region (e.g., `us-east-1`)
- **Confirm changes before deploy**: Y
- **Allow SAM CLI IAM role creation**: Y
- **Disable rollback**: N
- **Save arguments to configuration file**: Y
- **SAM configuration file**: `samconfig.toml`
- **SAM configuration environment**: `default`

The deployment will:
- Create 3 Lambda functions
- Create 2 DynamoDB tables
- Create 1 S3 bucket
- Create API Gateway
- Set up EventBridge schedule
- Configure CloudWatch alarms

**Note the API endpoint URL from the outputs!**

## Step 4: Verify Backend Deployment

```bash
# List Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `TeamRiskAnalysis`)].FunctionName'

# Check DynamoDB tables
aws dynamodb list-tables --query 'TableNames[?contains(@, `Team`)]'

# Test API endpoint
curl https://your-api-gateway-url.execute-api.region.amazonaws.com/prod/api/risks?team_id=demo-team-001
```

## Step 5: Configure Frontend

```bash
cd frontend

# Copy environment template
cp .env.example .env

# Edit .env and add your API endpoint
# VITE_API_BASE_URL=https://your-api-gateway-url.execute-api.region.amazonaws.com/prod
```

## Step 6: Run Frontend Locally

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Open `http://localhost:5173` in your browser.

## Step 7: Test the System

1. **Enable Mock Data Mode** in the frontend
2. **Select a scenario** (e.g., "Overloaded Team")
3. **View the radar chart** and risk list
4. **Click on a risk** to see details and recommendations
5. **Toggle language** between English and Spanish

## Optional: Deploy Frontend to S3 + CloudFront

### Build Frontend

```bash
cd frontend
npm run build
```

### Create S3 Bucket for Static Hosting

```bash
aws s3 mb s3://your-unique-bucket-name
aws s3 website s3://your-unique-bucket-name --index-document index.html
```

### Upload Build

```bash
aws s3 sync dist/ s3://your-unique-bucket-name --acl public-read
```

### Configure CloudFront (Optional)

For HTTPS and better performance, create a CloudFront distribution pointing to your S3 bucket.

## Updating the Deployment

After making changes:

```bash
# Rebuild and deploy
sam build
sam deploy
```

## Monitoring

### CloudWatch Logs

```bash
# View Ingest Lambda logs
aws logs tail /aws/lambda/TeamRiskAnalysis-Ingest --follow

# View Analyze Lambda logs
aws logs tail /aws/lambda/TeamRiskAnalysis-Analyze --follow

# View Query Lambda logs
aws logs tail /aws/lambda/TeamRiskAnalysis-Query --follow
```

### CloudWatch Metrics

Go to AWS Console → CloudWatch → Dashboards to view:
- Lambda invocations and errors
- DynamoDB read/write capacity
- API Gateway requests and latency
- Bedrock invocations

## Troubleshooting

### Bedrock Access Denied

**Error**: `AccessDeniedException` when calling Bedrock

**Solution**:
1. Verify Bedrock model access is enabled in AWS Console
2. Check IAM permissions include `bedrock:InvokeModel`
3. Ensure you're using the correct model ID in `template.yaml`

### Lambda Timeout

**Error**: Lambda function times out

**Solution**:
- Increase timeout in `template.yaml` (Analyze Lambda already has 90s)
- Check CloudWatch logs for specific errors
- Verify network connectivity to Bedrock

### CORS Errors

**Error**: CORS policy blocking frontend requests

**Solution**:
- Verify API Gateway CORS configuration in `template.yaml`
- Check that `VITE_API_BASE_URL` in frontend `.env` is correct
- Ensure API Gateway stage is deployed

### DynamoDB Throttling

**Error**: `ProvisionedThroughputExceededException`

**Solution**:
- Tables use pay-per-request billing, so this shouldn't happen
- Check CloudWatch metrics for unusual traffic patterns
- Verify table configuration in AWS Console

## Cost Management

### Monitor Costs

```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

### Set Up Billing Alerts

1. Go to AWS Console → Billing → Budgets
2. Create a budget for your expected monthly cost
3. Set up email alerts at 80% and 100% thresholds

## Cleanup

To delete all resources:

```bash
# Delete SAM stack
sam delete

# Verify deletion
aws cloudformation list-stacks --query 'StackSummaries[?StackName==`team-risk-analysis`]'
```

**Note**: S3 bucket must be empty before deletion. If deployment fails to delete:

```bash
# Empty S3 bucket
aws s3 rm s3://team-risk-snapshots-YOUR-ACCOUNT-ID --recursive

# Delete stack again
sam delete
```

## Security Best Practices

1. **Use IAM roles** with least-privilege permissions
2. **Enable CloudTrail** for audit logging
3. **Rotate AWS credentials** regularly
4. **Use AWS Secrets Manager** for sensitive configuration
5. **Enable MFA** on AWS account
6. **Review IAM policies** periodically

## Next Steps

- Set up CI/CD pipeline for automated deployments
- Configure custom domain for API Gateway
- Add authentication (Cognito, API keys)
- Set up CloudWatch dashboards for monitoring
- Implement automated backups for DynamoDB

## Support

For issues or questions:
- Check CloudWatch logs for errors
- Review AWS service quotas
- Open an issue on GitHub
- Consult AWS documentation

---

**Deployment complete!** Your AI Risk Radar is now running on AWS.
