# Query Lambda

Lambda function for retrieving risk data and recommendations for the dashboard.

## Purpose

The Query Lambda provides the GET /api/risks endpoint that the frontend dashboard uses to fetch:
- Latest risk dimension values (radar chart data)
- List of detected risks with severity levels
- Language-specific recommendations (Spanish or English)
- Last analysis timestamp

## API Specification

### Endpoint

```
GET /api/risks?team_id={id}&language={es|en}
```

### Query Parameters

- `team_id` (required): Team identifier
- `language` (optional): Language code for recommendations ('en' or 'es', defaults to 'en')

### Response Format

```json
{
  "team_id": "team-001",
  "last_analysis": "2024-01-15T10:30:00Z",
  "risk_dimensions": {
    "delivery_cadence": 45.5,
    "knowledge_concentration": 72.3,
    "dependency_risk": 38.1,
    "workload_distribution": 55.0,
    "attrition_signal": 28.7
  },
  "risks": [
    {
      "risk_id": "uuid",
      "dimension": "knowledge_concentration",
      "severity": "high",
      "description": "Knowledge is concentrated in a few team members...",
      "detected_at": "2024-01-15T10:30:00Z",
      "recommendations": [
        "Implement pair programming sessions",
        "Create documentation for critical systems"
      ]
    }
  ]
}
```

### Error Responses

**400 Bad Request** - Missing or invalid parameters:
```json
{
  "status": "error",
  "message": "team_id query parameter is required"
}
```

**500 Internal Server Error** - Server-side error:
```json
{
  "status": "error",
  "message": "Internal server error: ..."
}
```

## Implementation Details

### Data Flow

1. Parse query parameters from API Gateway event
2. Validate team_id and language parameters
3. Query DynamoDB RiskRecords table for latest risks
4. Extract signal values from most recent risk record
5. Filter recommendations by requested language
6. Format response for dashboard consumption
7. Return JSON response with CORS headers

### Language Filtering

The handler filters recommendations based on the requested language:
- `language=en`: Returns `description_en` and `recommendations_en`
- `language=es`: Returns `description_es` and `recommendations_es`

This ensures the dashboard only receives content in the selected language.

### Data Conversion

DynamoDB stores numeric values as Decimal types. The handler converts:
- Signal dimension values (Decimal → float)
- Any nested Decimal values in recommendations

This ensures proper JSON serialization for the API response.

## Requirements Validation

This Lambda satisfies:
- **Requirement 7.2**: Shows recommendations in user's selected language
- **Requirement 7.4**: Shows timestamp when risk was detected

## Testing

Run unit tests:
```bash
cd backend
pytest tests/test_query_lambda.py -v
```

## Environment Variables

- `RISK_RECORDS_TABLE`: DynamoDB table name for risk records (defaults to 'RiskRecords')
- `AWS_REGION`: AWS region (defaults to 'us-east-1')

## Dependencies

- boto3: AWS SDK for DynamoDB access
- backend.data_access.dynamodb_client: DynamoDB client wrapper
