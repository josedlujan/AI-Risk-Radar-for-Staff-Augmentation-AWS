.PHONY: help validate build deploy-dev deploy-prod test-local cleanup-dev cleanup-prod logs-ingest logs-analyze logs-query

help:
	@echo "Team Risk Analysis System - Makefile Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make validate      - Validate SAM template and check files"
	@echo "  make build         - Build SAM application"
	@echo "  make deploy-dev    - Deploy to development environment"
	@echo "  make deploy-prod   - Deploy to production environment"
	@echo "  make test-local    - Run local API for testing"
	@echo "  make cleanup-dev   - Remove development stack"
	@echo "  make cleanup-prod  - Remove production stack"
	@echo "  make logs-ingest   - Tail Ingest Lambda logs"
	@echo "  make logs-analyze  - Tail Analyze Lambda logs"
	@echo "  make logs-query    - Tail Query Lambda logs"
	@echo "  make test          - Run backend tests"
	@echo ""

validate:
	@./scripts/validate.sh

build:
	@sam build --use-container

deploy-dev:
	@./scripts/deploy.sh dev

deploy-prod:
	@./scripts/deploy.sh prod

test-local:
	@./scripts/test-local.sh

cleanup-dev:
	@./scripts/cleanup.sh dev

cleanup-prod:
	@./scripts/cleanup.sh prod

logs-ingest:
	@aws logs tail /aws/lambda/TeamRiskAnalysis-Ingest --follow

logs-analyze:
	@aws logs tail /aws/lambda/TeamRiskAnalysis-Analyze --follow

logs-query:
	@aws logs tail /aws/lambda/TeamRiskAnalysis-Query --follow

test:
	@cd backend && pytest -v

test-property:
	@cd backend && pytest -v -m property_test

test-unit:
	@cd backend && pytest -v -m "not property_test"
