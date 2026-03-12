"""Lambda handler for team signal ingestion endpoint."""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from models.team_signal import TeamSignal, SignalMetadata
from validation.team_signal_validator import validate_team_signal
from data_access.dynamodb_client import DynamoDBClient
from pydantic import ValidationError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb_client = DynamoDBClient()


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for POST /api/signals endpoint.
    
    Validates incoming team signals and stores them in DynamoDB.
    
    Args:
        event: API Gateway event containing request body
        context: Lambda context object
        
    Returns:
        API Gateway response with status and message
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        logger.info(f"Received signal ingestion request for team: {body.get('team_id')}")
        
        # Validate team signal using validation module
        validation_result = validate_team_signal(body)
        
        if not validation_result.is_valid:
            # Log validation failure for audit purposes
            logger.warning(
                f"Validation failed for team signal",
                extra={
                    'team_id': body.get('team_id'),
                    'errors': validation_result.errors,
                    'rejected_fields': validation_result.rejected_fields,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Return appropriate error response
            error_code = _determine_error_code(validation_result)
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'error': error_code,
                    'message': _format_error_message(validation_result),
                    'errors': validation_result.errors,
                    'rejected_fields': validation_result.rejected_fields
                })
            }
        
        # Parse and validate using Pydantic model
        try:
            # Extract signals from body
            signals_data = {
                'team_id': body['team_id'],
                'timestamp': body.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'delivery_cadence': body['delivery_cadence'],
                'knowledge_concentration': body['knowledge_concentration'],
                'dependency_risk': body['dependency_risk'],
                'workload_distribution': body['workload_distribution'],
                'attrition_signal': body['attrition_signal'],
                'metadata': body['metadata']
            }
            
            team_signal = TeamSignal(**signals_data)
            
        except ValidationError as e:
            logger.error(f"Pydantic validation error: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'error': 'INVALID_DATA_FORMAT',
                    'message': 'Invalid data format',
                    'details': str(e)
                })
            }
        except KeyError as e:
            logger.error(f"Missing required field: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'error': 'MISSING_REQUIRED_FIELD',
                    'message': f'Missing required field: {str(e)}'
                })
            }
        
        # Store validated signal in DynamoDB
        try:
            dynamodb_client.put_team_signal(team_signal)
            
            signal_id = f"{team_signal.team_id}_{team_signal.timestamp.isoformat()}"
            
            logger.info(
                f"Successfully stored team signal",
                extra={
                    'signal_id': signal_id,
                    'team_id': team_signal.team_id,
                    'timestamp': team_signal.timestamp.isoformat()
                }
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'success',
                    'signal_id': signal_id,
                    'message': 'Team signal successfully ingested'
                })
            }
            
        except Exception as e:
            logger.error(
                f"Failed to store team signal in DynamoDB: {str(e)}",
                extra={
                    'team_id': team_signal.team_id,
                    'error': str(e)
                }
            )
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'error': 'STORAGE_FAILURE',
                    'message': 'Failed to store team signal'
                })
            }
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'error',
                'error': 'INVALID_JSON',
                'message': 'Invalid JSON in request body'
            })
        }
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'error',
                'error': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            })
        }


def _determine_error_code(validation_result) -> str:
    """
    Determine the appropriate error code based on validation errors.
    
    Args:
        validation_result: ValidationResult from validation module
        
    Returns:
        Error code string
    """
    errors_text = ' '.join(validation_result.errors).lower()
    
    if 'individual' in errors_text or 'identifier' in errors_text:
        return 'INDIVIDUAL_DATA_REJECTED'
    elif 'missing' in errors_text and 'dimension' in errors_text:
        return 'INCOMPLETE_DIMENSIONS'
    elif 'metadata' in errors_text:
        return 'INVALID_METADATA'
    else:
        return 'VALIDATION_FAILED'


def _format_error_message(validation_result) -> str:
    """
    Format a user-friendly error message based on validation errors.
    
    Args:
        validation_result: ValidationResult from validation module
        
    Returns:
        Formatted error message string
    """
    errors_text = ' '.join(validation_result.errors).lower()
    
    if 'individual' in errors_text or 'identifier' in errors_text:
        return "Individual engineer data not permitted. Submit aggregated team-level metrics only."
    elif 'missing' in errors_text and 'dimension' in errors_text:
        return "All five risk dimensions required"
    elif 'metadata' in errors_text:
        return "Aggregation metadata required"
    else:
        return "Validation failed"
