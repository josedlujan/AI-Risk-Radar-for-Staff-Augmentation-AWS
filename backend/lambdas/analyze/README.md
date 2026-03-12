# Analyze Lambda Function

## Overview

The Analyze Lambda function is the core of the Team Risk Analysis System. It performs AI-powered risk analysis on team signals using Amazon Bedrock's Claude 3.5 Sonnet model.

## Functionality

This Lambda handler:
1. Fetches recent team signals from DynamoDB (last 24 hours)
2. Invokes BedrockAnalyzer to identify risks across five dimensions
3. Stores risk records in DynamoDB with bilingual recommendations
4. Creates historical snapshots in S3 for trend analysis

## Trigger Sources

### EventBridge Scheduled Rule
Automated analysis runs on a schedule (e.g., daily, weekly).

**Event Format:**
```json
{
  "source": "aws.events",
  "detail": {
    "team_id": "team-001"
  }
}
```

### API Gateway (On-Demand)
Manual analysis triggered via POST /api/analyze endpoint.

**Request Format:**
```json
{
  "team_id": "team-001",
  "analysis_type": "on_demand"
}
```

## Response Format

**Success Response (200):**
```json
{
  "status": "success",
  "analysis_id": "uuid",
  "team_id": "team-001",
  "analysis_type": "scheduled|on_demand",
  "risks_detected": 3,
  "snapshot_url": "s3://bucket/path/to/snapshot.json",
  "analysis_duration_ms": 5000
}
```

**Error Response (400/404/500):**
```json
{
  "status": "error",
  "message": "Error description"
}
```

## Environment Variables

- `TEAM_SIGNALS_TABLE`: DynamoDB table name for team signals (default: "TeamSignals")
- `RISK_RECORDS_TABLE`: DynamoDB table name for risk records (default: "RiskRecords")
- `SNAPSHOTS_BUCKET`: S3 bucket name for snapshots (default: "team-risk-snapshots")
- `DEFAULT_TEAM_ID`: Default team ID for scheduled events (default: "team-001")
- `AWS_REGION`: AWS region for services (default: "us-east-1")

## IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Query",
        "dynamodb:PutItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/TeamSignals",
        "arn:aws:dynamodb:*:*:table/RiskRecords"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::team-risk-snapshots/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
    }
  ]
}
```

## Error Handling

### Missing Team ID (400)
Returned when `team_id` is not provided in the request.

### No Signals Found (404)
Returned when no team signals exist for the specified team in the last 24 hours.

### Bedrock Errors (500)
- **Timeout**: Retries up to 3 times with exponential backoff
- **Rate Limiting**: Retries with exponential backoff
- **Invalid Response**: Returns error after parsing failure

### DynamoDB Errors (500)
- Automatic retries via AWS SDK
- Errors logged for monitoring

### S3 Errors (500)
- Retries up to 3 times
- Analysis continues even if snapshot fails (non-critical)

## Testing

Run unit tests:
```bash
cd backend
python3 -m pytest tests/test_analyze_lambda.py -v
```

## Dependencies

- `boto3`: AWS SDK for Python
- `backend.ai.bedrock_analyzer`: Bedrock integration module
- `backend.data_access.dynamodb_client`: DynamoDB client wrapper
- `backend.data_access.s3_client`: S3 client wrapper
- `backend.models`: Data models (TeamSignal, RiskRecord, Snapshot)

## Performance Considerations

- **Lookback Period**: Fetches signals from last 24 hours (configurable)
- **Signal Limit**: Retrieves up to 10 most recent signals
- **Bedrock Timeout**: 30 seconds per analysis (with retries)
- **Expected Duration**: 5-15 seconds for typical analysis

## Monitoring

Key CloudWatch metrics to monitor:
- Lambda execution duration
- Lambda error rate
- Bedrock invocation latency
- DynamoDB throttling events
- S3 upload failures

## Related Components

- **Ingest Lambda**: Stores team signals that this function analyzes
- **Query Lambda**: Retrieves risk records created by this function
- **BedrockAnalyzer**: AI analysis engine
- **DynamoDB Tables**: TeamSignals and RiskRecords
- **S3 Bucket**: Historical snapshots storage
