# AI Risk Radar for Staff Augmentation

A serverless system that analyzes team-level engineering signals using Claude Sonnet 4 on Amazon Bedrock to detect systemic risks before they become crises—without individual surveillance.

![AWS](https://img.shields.io/badge/AWS-Serverless-orange)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![React](https://img.shields.io/badge/React-18-61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6)
![License](https://img.shields.io/badge/License-MIT-green)

## Overview

Engineering organizations don't fail because of bad code. They fail because of invisible system-level risks that compound silently until it's too late. AI Risk Radar makes those risks visible through aggregated team-level signals across five critical dimensions:

- **Delivery Cadence**: Sprint velocity, release frequency, cycle time
- **Knowledge Concentration**: Bus factor, expertise distribution, documentation coverage
- **Dependency Risk**: External blockers, cross-team dependencies, integration complexity
- **Workload Distribution**: Task balance, overtime patterns, capacity utilization
- **Attrition Signal**: Turnover indicators, engagement metrics, retention risk

The system ingests team-level metrics, runs them through Claude Sonnet 4 on Amazon Bedrock, and generates actionable insights in both Spanish and English.

## Architecture

```
External Systems → API Gateway → Lambda (Ingest) → DynamoDB (TeamSignals)
                                                  ↓
                                          EventBridge (Daily)
                                                  ↓
                                          Lambda (Analyze) ← → Bedrock (Claude Sonnet 4)
                                                  ↓
                                          DynamoDB (RiskRecords) + S3 (Snapshots)
                                                  ↓
React Frontend ← API Gateway ← Lambda (Query) ← DynamoDB
```

### AWS Services

- **AWS Lambda** (3 functions): Ingest, Analyze, Query
- **Amazon DynamoDB** (2 tables): TeamSignals, RiskRecords
- **Amazon S3**: Historical snapshots (90-day lifecycle)
- **Amazon API Gateway**: REST API with CORS
- **Amazon EventBridge**: Scheduled daily analysis
- **Amazon CloudWatch**: Logs, metrics, alarms
- **Amazon Bedrock**: Claude Sonnet 4 for AI analysis

## Features

- **Privacy-First Design**: Only accepts pre-aggregated team-level data, rejects individual identifiers
- **AI-Powered Analysis**: Claude Sonnet 4 analyzes patterns and generates contextual recommendations
- **Bilingual Support**: Full Spanish and English support for global teams
- **Real-time Dashboard**: React-based UI with radar charts and risk visualization
- **Mock Data Mode**: Built-in scenarios for demos (healthy, overloaded, knowledge silo, etc.)
- **Serverless Architecture**: Fully managed, auto-scaling, pay-per-use
- **Property-Based Testing**: 177+ tests including Hypothesis-based validation

## Prerequisites

- **AWS Account** with appropriate permissions
- **AWS CLI** configured with credentials
- **AWS SAM CLI** for deployment
- **Python 3.13** for backend development
- **Node.js 18+** for frontend development
- **Amazon Bedrock** access to Claude Sonnet 4

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/[your-username]/AI-Risk-Radar-for-Staff-Augmentation.git
cd AI-Risk-Radar-for-Staff-Augmentation
```

### 2. Deploy Backend to AWS

```bash
# Build and deploy with SAM
sam build
sam deploy --guided

# Note the API endpoint from outputs
```

### 3. Configure Frontend

```bash
cd frontend

# Create .env file
echo "VITE_API_BASE_URL=https://your-api-gateway-url.execute-api.region.amazonaws.com/prod" > .env

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access Dashboard

Open `http://localhost:5173` in your browser.

## API Endpoints

### POST /api/signals
Ingest team-level signals.

```json
{
  "team_id": "team-001",
  "delivery_cadence": 45.0,
  "knowledge_concentration": 55.0,
  "dependency_risk": 40.0,
  "workload_distribution": 50.0,
  "attrition_signal": 35.0,
  "metadata": {
    "team_size": 8,
    "project_count": 3,
    "aggregation_period": "weekly"
  }
}
```

### POST /api/analyze
Trigger analysis for a team (also runs daily via EventBridge).

```json
{
  "team_id": "team-001"
}
```

### GET /api/risks?team_id=team-001
Query detected risks for a team.

## Development

### Backend Testing

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Project Structure

```
.
├── backend/
│   ├── ai/                    # Bedrock integration
│   ├── data_access/           # DynamoDB and S3 clients
│   ├── lambdas/               # Lambda function handlers
│   │   ├── analyze/
│   │   ├── ingest/
│   │   └── query/
│   ├── models/                # Pydantic data models
│   ├── mock_data/             # Mock data generator
│   ├── validation/            # Input validation
│   └── tests/                 # Unit and property-based tests
├── frontend/
│   └── src/
│       ├── api/               # API client
│       ├── components/        # React components
│       ├── contexts/          # React contexts
│       └── types/             # TypeScript types
├── scripts/                   # Deployment and setup scripts
├── template.yaml              # AWS SAM template
├── samconfig.toml             # SAM configuration
└── cloudwatch-dashboard.json  # CloudWatch dashboard definition
```

## Configuration

### Environment Variables (Backend)

Set in `template.yaml`:

- `TEAM_SIGNALS_TABLE`: DynamoDB table for signals
- `RISK_RECORDS_TABLE`: DynamoDB table for risks
- `SNAPSHOTS_BUCKET`: S3 bucket for snapshots
- `BEDROCK_MODEL_ID`: Bedrock model identifier
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

### Environment Variables (Frontend)

Set in `frontend/.env`:

- `VITE_API_BASE_URL`: API Gateway endpoint URL

## Cost Estimation

### Development (Low Usage)
- Lambda: ~$5-10/month
- DynamoDB: ~$2-5/month (pay-per-request)
- S3: ~$1-2/month
- Bedrock: ~$2-8/month (depends on analysis frequency)
- **Total: $10-25/month**

### Production (Moderate Usage)
- Lambda: ~$20-40/month
- DynamoDB: ~$15-30/month
- S3: ~$5-10/month
- Bedrock: ~$40-85/month
- **Total: $80-165/month**

## Security

- **No Individual Data**: System rejects payloads with individual identifiers
- **IAM Roles**: All services use least-privilege IAM roles
- **Encryption**: Data encrypted at rest (DynamoDB, S3) and in transit (HTTPS)
- **CORS**: API Gateway configured with appropriate CORS policies
- **TTL**: Automatic data deletion after 90 days

## Privacy Philosophy

This system operates exclusively on team-level aggregates. Individual engineer data must be aggregated before reaching this system. The validation layer enforces this boundary by rejecting any payload containing patterns like:

- `user_id`, `engineer_id`, `employee_id`
- `email`, `name`, `username`
- Any individual identifiers

This isn't just a feature—it's a philosophical stance. Trust is fragile. Individual monitoring creates surveillance culture that destroys trust and makes data useless.

## Testing

The project includes comprehensive testing:

- **Unit Tests**: 150+ tests for core functionality
- **Property-Based Tests**: Hypothesis-based validation of invariants
- **Integration Tests**: End-to-end testing with AWS services
- **Mock Data**: Realistic scenarios for testing and demos

Run tests:

```bash
cd backend
pytest
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for the AWS 10,000 AIdeas Competition
- Powered by Amazon Bedrock and Claude Sonnet 4
- Developed using Kiro AI-powered IDE

## Contact

For questions, issues, or feedback, please open an issue on GitHub.

---

**Built with AWS | Powered by Bedrock | Designed for Engineering Leaders**
