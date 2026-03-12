# Deployment Scripts

This directory contains shell scripts for deploying and managing the Team Risk Analysis System on AWS.

## Scripts Overview

### deploy.sh
**Purpose**: Build and deploy the SAM application to AWS

**Usage**:
```bash
./scripts/deploy.sh [environment]
```

**Parameters**:
- `environment` (optional): `dev` or `prod` (default: `dev`)

**Examples**:
```bash
./scripts/deploy.sh dev      # Deploy to development
./scripts/deploy.sh prod     # Deploy to production (with confirmation)
```

**What it does**:
1. Validates AWS CLI and SAM CLI are installed
2. Builds Lambda functions and layers using Docker
3. Packages and uploads artifacts to S3
4. Deploys CloudFormation stack
5. Displays stack outputs (API endpoint, resource names)

---

### validate.sh
**Purpose**: Validate SAM template and check for common issues

**Usage**:
```bash
./scripts/validate.sh
```

**What it does**:
1. Validates SAM template syntax
2. Checks required files exist (handlers, requirements.txt)
3. Validates Python syntax in Lambda handlers
4. Reports any issues found

**When to use**:
- Before deploying to catch errors early
- After modifying the SAM template
- As part of CI/CD pipeline

---

### cleanup.sh
**Purpose**: Remove all AWS resources created by the deployment

**Usage**:
```bash
./scripts/cleanup.sh [environment]
```

**Parameters**:
- `environment` (optional): `dev` or `prod` (default: `dev`)

**Examples**:
```bash
./scripts/cleanup.sh dev     # Remove development stack
./scripts/cleanup.sh prod    # Remove production stack
```

**What it does**:
1. Prompts for confirmation (requires typing "yes")
2. Empties S3 bucket (required before deletion)
3. Deletes CloudFormation stack
4. Waits for deletion to complete

**Warning**: This permanently deletes all data including:
- Lambda functions
- DynamoDB tables and all stored data
- S3 bucket and all snapshots
- CloudWatch logs

---

### test-local.sh
**Purpose**: Run Lambda functions locally for testing

**Usage**:
```bash
./scripts/test-local.sh
```

**What it does**:
1. Builds SAM application
2. Starts local API Gateway at `http://127.0.0.1:3000`
3. Makes all endpoints available for testing

**Available endpoints**:
- `POST http://127.0.0.1:3000/api/signals` - Ingest team signals
- `POST http://127.0.0.1:3000/api/analyze` - Trigger analysis
- `GET http://127.0.0.1:3000/api/risks` - Query risk data

**Requirements**:
- Docker must be running
- SAM CLI installed

**To stop**: Press `Ctrl+C`

---

### setup-dashboard.sh
**Purpose**: Create CloudWatch dashboard for monitoring

**Usage**:
```bash
./scripts/setup-dashboard.sh [environment]
```

**Parameters**:
- `environment` (optional): `dev` or `prod` (default: `dev`)

**Examples**:
```bash
./scripts/setup-dashboard.sh dev     # Create dev dashboard
./scripts/setup-dashboard.sh prod    # Create prod dashboard
```

**What it does**:
1. Creates CloudWatch dashboard with metrics for:
   - Lambda invocations and errors
   - Lambda duration
   - DynamoDB capacity usage
   - API Gateway requests and errors
   - API Gateway latency
2. Provides link to view dashboard in AWS Console

---

## Common Workflows

### First-time Deployment
```bash
# 1. Validate everything is correct
./scripts/validate.sh

# 2. Deploy to development
./scripts/deploy.sh dev

# 3. Set up monitoring dashboard
./scripts/setup-dashboard.sh dev

# 4. Test the API
export API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name team-risk-analysis-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

curl $API_ENDPOINT/api/risks?team_id=test-team
```

### Local Development
```bash
# 1. Start local API
./scripts/test-local.sh

# 2. In another terminal, test endpoints
curl -X POST http://127.0.0.1:3000/api/signals \
  -H "Content-Type: application/json" \
  -d @test-data/sample-signal.json
```

### Update Deployment
```bash
# 1. Make changes to code or template

# 2. Validate changes
./scripts/validate.sh

# 3. Deploy updated version
./scripts/deploy.sh dev
```

### Production Deployment
```bash
# 1. Test in development first
./scripts/deploy.sh dev

# 2. Verify everything works
# ... run tests ...

# 3. Deploy to production (with confirmation)
./scripts/deploy.sh prod

# 4. Set up production monitoring
./scripts/setup-dashboard.sh prod
```

### Cleanup
```bash
# Remove development environment
./scripts/cleanup.sh dev

# Remove production environment (be careful!)
./scripts/cleanup.sh prod
```

## Troubleshooting

### Script Permission Denied
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### AWS CLI Not Found
```bash
# Install AWS CLI
brew install awscli  # macOS
# or download from: https://aws.amazon.com/cli/

# Configure credentials
aws configure
```

### SAM CLI Not Found
```bash
# Install SAM CLI
brew install aws-sam-cli  # macOS
# or download from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
```

### Docker Not Running
```bash
# Start Docker Desktop
# Then verify:
docker ps
```

### Deployment Fails
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check CloudFormation events for details
aws cloudformation describe-stack-events \
  --stack-name team-risk-analysis-dev \
  --max-items 10
```

## Environment Variables

Scripts use these environment variables (optional):

- `AWS_PROFILE`: AWS CLI profile to use (default: default)
- `AWS_REGION`: AWS region for deployment (default: us-east-1)
- `SAM_CLI_TELEMETRY`: Disable SAM telemetry (set to 0)

**Example**:
```bash
export AWS_PROFILE=my-profile
export AWS_REGION=us-west-2
./scripts/deploy.sh dev
```

## CI/CD Integration

These scripts can be integrated into CI/CD pipelines:

**GitHub Actions Example**:
```yaml
- name: Validate SAM template
  run: ./scripts/validate.sh

- name: Deploy to staging
  run: ./scripts/deploy.sh dev
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

**GitLab CI Example**:
```yaml
deploy:
  script:
    - ./scripts/validate.sh
    - ./scripts/deploy.sh dev
  only:
    - main
```

## Best Practices

1. **Always validate before deploying**: Run `validate.sh` first
2. **Test locally when possible**: Use `test-local.sh` for quick iterations
3. **Deploy to dev first**: Test in development before production
4. **Monitor deployments**: Set up CloudWatch dashboards
5. **Clean up unused stacks**: Remove old development stacks to save costs
6. **Use version control**: Commit changes before deploying
7. **Document changes**: Update CHANGELOG.md with deployment notes

## Support

For issues with scripts:
1. Check script output for error messages
2. Verify prerequisites are installed
3. Check AWS CloudFormation console for stack events
4. Review CloudWatch logs for Lambda errors
5. Consult DEPLOYMENT.md for detailed troubleshooting
