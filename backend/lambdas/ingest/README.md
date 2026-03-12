# Ingest Lambda Handler

Lambda function for ingesting team-level signals via POST /api/signals endpoint.

## Overview

This Lambda handler validates and stores aggregated team-level metrics in DynamoDB. It enforces privacy by rejecting any data containing individual engineer identifiers.

## API Endpoint

**POST /api/signals**

### Request Body

```json
{
  "team_id": "string",
  "timestamp": "ISO8601 string (optional, defaults to current time)",
  "delivery_cadence": 0-100,
  "knowledge_concentration": 0-100,
  "dependency_risk": 0-100,
  "workload_distribution": 0-100,
  "attrition_signal": 0-100,
  "metadata": {
    "team_size": "integer > 0",
    "project_count": "integer > 0",
    "aggregation_period": "string (e.g., 'weekly', 'daily')"
  }
}
```

### Success Response

**Status Code:** 200

```json
{
  "status": "success",
  "signal_id": "team-alpha_2024-01-15T10:00:00Z",
  "message": "Team signal successfully ingested"
}
```

### Error Responses

#### Individual Data Rejected

**Status Code:** 400

```json
{
  "status": "error",
  "error": "INDIVIDUAL_DATA_REJECTED",
  "message": "Individual engineer data not permitted. Submit aggregated team-level metrics only.",
  "errors": ["Field 'notes' contains individual identifier pattern: 'user_'"],
  "rejected_fields": ["notes"]
}
```

#### Incomplete Dimensions

**Status Code:** 400

```json
{
  "status": "error",
  "error": "INCOMPLETE_DIMENSIONS",
  "message": "All five risk dimensions required",
  "errors": ["Missing required dimension: 'attrition_signal'"],
  "rejected_fields": ["attrition_signal"]
}
```

#### Invalid Metadata

**Status Code:** 400

```json
{
  "status": "error",
  "error": "INVALID_METADATA",
  "message": "Aggregation metadata required",
  "errors": ["Missing required metadata field: 'team_size'"],
  "rejected_fields": ["metadata.team_size"]
}
```

#### Storage Failure

**Status Code:** 500

```json
{
  "status": "error",
  "error": "STORAGE_FAILURE",
  "message": "Failed to store team signal"
}
```

## Validation Rules

### Privacy Enforcement (Requirements 1.1, 1.2, 10.1, 10.2)

The handler rejects any data containing individual engineer identifiers, including:
- `user_`, `engineer_`, `employee_`, `developer_`, `member_` prefixes
- Email addresses (containing `@` or `email`)
- Individual names or person identifiers

### Five Dimensions Required (Requirements 1.5, 2.5)

All five risk dimensions must be present with numeric values between 0-100:
- `delivery_cadence`
- `knowledge_concentration`
- `dependency_risk`
- `workload_distribution`
- `attrition_signal`

### Aggregation Metadata (Requirements 1.3, 1.4)

The `metadata` object must contain:
- `team_size`: Integer greater than 0
- `project_count`: Integer greater than 0
- `aggregation_period`: Non-empty string

## Environment Variables

- `TEAM_SIGNALS_TABLE`: DynamoDB table name for storing team signals (default: "TeamSignals")
- `AWS_REGION`: AWS region for DynamoDB (default: "us-east-1")

## Testing

Run unit tests:
```bash
cd backend
python3 -m pytest tests/test_ingest_lambda.py -v
```

Run integration tests:
```bash
python3 -m pytest tests/test_ingest_integration.py -v
```

## Logging

The handler logs:
- Successful ingestions with signal_id and team_id
- Validation failures with error details and rejected fields (for audit purposes per Requirement 10.5)
- DynamoDB storage errors
- All errors with appropriate context

## CORS Support

All responses include CORS headers:
- `Access-Control-Allow-Origin: *`
- `Content-Type: application/json`
