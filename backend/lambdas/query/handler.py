"""Lambda handler for risk data retrieval."""

import json
from typing import Dict, Any, List, Optional
from decimal import Decimal

from data_access.dynamodb_client import DynamoDBClient


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for querying risk data.
    
    Endpoint: GET /api/risks?team_id={id}&language={es|en}
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
    
    Returns:
        Response dict with risk data formatted for dashboard
    """
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        team_id = query_params.get('team_id')
        language = query_params.get('language', 'en')
        
        # Validate inputs
        if not team_id:
            return _error_response(400, "team_id query parameter is required")
        
        if language not in ['en', 'es']:
            return _error_response(400, "language must be 'en' or 'es'")
        
        # Initialize DynamoDB client
        dynamodb_client = DynamoDBClient()
        
        # Query latest risk records for the team
        risk_items = dynamodb_client.query_risk_records(
            team_id=team_id,
            limit=50  # Limit to most recent 50 risks
        )
        
        if not risk_items:
            # Return empty response if no risks found
            return _success_response({
                'team_id': team_id,
                'last_analysis': None,
                'risk_dimensions': {},
                'risks': []
            })
        
        # Extract signal values from the most recent risk
        latest_risk = risk_items[0]
        signal_values = latest_risk.get('signal_values', {})
        
        # Convert Decimal to float for JSON serialization
        risk_dimensions = {
            'delivery_cadence': float(signal_values.get('delivery_cadence', 0)),
            'knowledge_concentration': float(signal_values.get('knowledge_concentration', 0)),
            'dependency_risk': float(signal_values.get('dependency_risk', 0)),
            'workload_distribution': float(signal_values.get('workload_distribution', 0)),
            'attrition_signal': float(signal_values.get('attrition_signal', 0)),
        }
        
        # Format risks for dashboard consumption
        risks = _format_risks(risk_items, language)
        
        # Get last analysis timestamp
        last_analysis = latest_risk.get('detected_at')
        
        # Return formatted response
        return _success_response({
            'team_id': team_id,
            'last_analysis': last_analysis,
            'risk_dimensions': risk_dimensions,
            'risks': risks
        })
        
    except Exception as e:
        print(f"Error in query Lambda: {str(e)}")
        return _error_response(500, f"Internal server error: {str(e)}")


def _format_risks(risk_items: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
    """
    Format risk records for dashboard consumption with language filtering.
    
    Args:
        risk_items: List of risk items from DynamoDB
        language: Language code ('en' or 'es')
    
    Returns:
        List of formatted risk dicts
    """
    formatted_risks = []
    
    for item in risk_items:
        # Select description and recommendations based on language
        description_key = f'description_{language}'
        recommendations_key = f'recommendations_{language}'
        
        formatted_risk = {
            'risk_id': item.get('risk_id'),
            'dimension': item.get('dimension'),
            'severity': item.get('severity'),
            'description': item.get(description_key, ''),
            'detected_at': item.get('detected_at'),
            'recommendations': _convert_decimals(item.get(recommendations_key, []))
        }
        
        formatted_risks.append(formatted_risk)
    
    return formatted_risks


def _convert_decimals(obj: Any) -> Any:
    """
    Recursively convert Decimal values to float for JSON serialization.
    
    Args:
        obj: Object to convert (dict, list, or primitive)
    
    Returns:
        Object with Decimals converted to float
    """
    if isinstance(obj, list):
        return [_convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


def _success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a success response for API Gateway.
    
    Args:
        data: Response data
    
    Returns:
        API Gateway response dict
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(data)
    }


def _error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create an error response for API Gateway.
    
    Args:
        status_code: HTTP status code
        message: Error message
    
    Returns:
        API Gateway response dict
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({
            'status': 'error',
            'message': message
        })
    }
