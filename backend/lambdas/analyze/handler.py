"""Lambda handler for risk analysis."""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from ai.bedrock_analyzer import BedrockAnalyzer
from data_access.dynamodb_client import DynamoDBClient
from data_access.s3_client import S3Client
from models.snapshot import Snapshot, SnapshotRisk, SnapshotMetadata


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for risk analysis.
    
    Triggered by:
    - EventBridge scheduled rule (automated analysis)
    - API Gateway POST /api/analyze (on-demand analysis)
    
    Args:
        event: Lambda event (EventBridge or API Gateway format)
        context: Lambda context
    
    Returns:
        Response dict with analysis results
    """
    try:
        # Parse input
        request_body = _parse_event(event)
        team_id = request_body.get('team_id')
        analysis_type = request_body.get('analysis_type', 'scheduled')
        
        if not team_id:
            return _error_response(400, "team_id is required")
        
        # Initialize clients
        dynamodb_client = DynamoDBClient()
        bedrock_analyzer = BedrockAnalyzer()
        s3_client = S3Client()
        
        # Fetch recent team signals
        signals_data = _fetch_recent_signals(dynamodb_client, team_id)
        
        if not signals_data:
            return _error_response(404, f"No signals found for team: {team_id}")
        
        # Extract signal values and metadata
        latest_signal = signals_data[0]
        signal_values = {
            'delivery_cadence': float(latest_signal.get('delivery_cadence', 0)),
            'knowledge_concentration': float(latest_signal.get('knowledge_concentration', 0)),
            'dependency_risk': float(latest_signal.get('dependency_risk', 0)),
            'workload_distribution': float(latest_signal.get('workload_distribution', 0)),
            'attrition_signal': float(latest_signal.get('attrition_signal', 0)),
        }
        
        metadata = latest_signal.get('metadata', {})
        
        # Invoke Bedrock analyzer
        analysis_result = bedrock_analyzer.analyze_team_signals(
            team_id=team_id,
            signals=signal_values,
            metadata=metadata
        )
        
        # Update risk records with signal values
        for risk in analysis_result.risks:
            risk.signal_values = signal_values
        
        # Store risk records in DynamoDB
        for risk in analysis_result.risks:
            dynamodb_client.put_risk_record(risk)
        
        # Create historical snapshot
        snapshot = _create_snapshot(
            team_id=team_id,
            signal_values=signal_values,
            risks=analysis_result.risks,
            metadata=metadata,
            analysis_duration_ms=analysis_result.analysis_duration_ms
        )
        
        # Store snapshot in S3
        snapshot_result = s3_client.put_snapshot(snapshot)
        
        # Return success response
        return _success_response({
            'status': 'success',
            'analysis_id': analysis_result.analysis_id,
            'team_id': team_id,
            'analysis_type': analysis_type,
            'risks_detected': analysis_result.risk_count,
            'snapshot_url': f"s3://{snapshot_result['bucket']}/{snapshot_result['key']}",
            'analysis_duration_ms': analysis_result.analysis_duration_ms,
        })
        
    except ValueError as e:
        # Validation or parsing errors
        return _error_response(400, str(e))
    
    except RuntimeError as e:
        # Bedrock or other runtime errors
        return _error_response(500, str(e))
    
    except Exception as e:
        # Unexpected errors
        print(f"Unexpected error in analyze Lambda: {str(e)}")
        return _error_response(500, f"Internal server error: {str(e)}")


def _parse_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Lambda event from EventBridge or API Gateway.
    
    Args:
        event: Lambda event
    
    Returns:
        Parsed request body
    """
    # Check if event is from API Gateway
    if 'body' in event:
        # API Gateway event
        body = event['body']
        if isinstance(body, str):
            return json.loads(body)
        return body
    
    # Check if event is from EventBridge
    elif 'source' in event and event['source'] == 'aws.events':
        # EventBridge scheduled event
        # Extract team_id from event detail if present
        detail = event.get('detail', {})
        return {
            'team_id': detail.get('team_id', os.environ.get('DEFAULT_TEAM_ID', 'team-001')),
            'analysis_type': 'scheduled'
        }
    
    # Direct invocation or test event
    else:
        return event


def _fetch_recent_signals(
    dynamodb_client: DynamoDBClient,
    team_id: str,
    lookback_hours: int = 24
) -> list:
    """
    Fetch recent team signals from DynamoDB.
    
    Args:
        dynamodb_client: DynamoDB client instance
        team_id: Team identifier
        lookback_hours: Hours to look back for signals
    
    Returns:
        List of signal items (most recent first)
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=lookback_hours)
    
    signals = dynamodb_client.query_team_signals(
        team_id=team_id,
        start_time=start_time,
        end_time=end_time,
        limit=10  # Get up to 10 most recent signals
    )
    
    return signals


def _create_snapshot(
    team_id: str,
    signal_values: Dict[str, float],
    risks: list,
    metadata: Dict[str, Any],
    analysis_duration_ms: int
) -> Snapshot:
    """
    Create a historical snapshot from analysis results.
    
    Args:
        team_id: Team identifier
        signal_values: Signal values for all five dimensions
        risks: List of RiskRecord instances
        metadata: Team metadata
        analysis_duration_ms: Analysis duration in milliseconds
    
    Returns:
        Snapshot instance
    """
    snapshot_risks = [
        SnapshotRisk(
            risk_id=risk.risk_id,
            dimension=risk.dimension,
            severity=risk.severity.value,
            description_en=risk.description_en,
            description_es=risk.description_es
        )
        for risk in risks
    ]
    
    snapshot_metadata = SnapshotMetadata(
        team_size=metadata.get('team_size', 0),
        project_count=metadata.get('project_count', 0),
        analysis_duration_ms=analysis_duration_ms
    )
    
    snapshot = Snapshot(
        team_id=team_id,
        signals=signal_values,
        risks=snapshot_risks,
        metadata=snapshot_metadata
    )
    
    return snapshot


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
