"""DynamoDB client wrapper for TeamSignals and RiskRecords table operations."""

import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from models.team_signal import TeamSignal
from models.risk_record import RiskRecord


class DynamoDBClient:
    """Wrapper for DynamoDB operations on TeamSignals and RiskRecords tables."""
    
    def __init__(
        self,
        team_signals_table_name: Optional[str] = None,
        risk_records_table_name: Optional[str] = None,
        region_name: str = "us-east-1"
    ):
        """
        Initialize DynamoDB client.
        
        Args:
            team_signals_table_name: Name of TeamSignals table (defaults to env var)
            risk_records_table_name: Name of RiskRecords table (defaults to env var)
            region_name: AWS region name
        """
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        
        self.team_signals_table_name = team_signals_table_name or os.environ.get(
            'TEAM_SIGNALS_TABLE', 'TeamSignals'
        )
        self.risk_records_table_name = risk_records_table_name or os.environ.get(
            'RISK_RECORDS_TABLE', 'RiskRecords'
        )
        
        self.team_signals_table = self.dynamodb.Table(self.team_signals_table_name)
        self.risk_records_table = self.dynamodb.Table(self.risk_records_table_name)
    
    # TeamSignals table operations
    
    def put_team_signal(self, team_signal: TeamSignal) -> Dict[str, Any]:
        """
        Store a team signal in DynamoDB with TTL for 90-day retention.
        
        Args:
            team_signal: TeamSignal instance to store
            
        Returns:
            Response from DynamoDB put operation
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        item = team_signal.to_dynamodb_item()
        
        # Add TTL for 90-day retention
        ttl_timestamp = int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())
        item['ttl'] = ttl_timestamp
        
        # Convert floats to Decimal for DynamoDB
        item = self._convert_floats_to_decimal(item)
        
        try:
            response = self.team_signals_table.put_item(Item=item)
            return response
        except ClientError as e:
            raise ClientError(
                error_response={
                    'Error': {
                        'Code': e.response['Error']['Code'],
                        'Message': f"Failed to store team signal: {e.response['Error']['Message']}"
                    }
                },
                operation_name='PutItem'
            )

    def query_team_signals(
        self,
        team_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query team signals for a specific team within a time range.
        
        Args:
            team_id: Team identifier
            start_time: Start of time range (optional)
            end_time: End of time range (optional)
            limit: Maximum number of items to return (optional)
            
        Returns:
            List of team signal items
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        try:
            key_condition = Key('PK').eq(f'TEAM#{team_id}')
            
            # Add time range filtering if provided
            if start_time and end_time:
                key_condition &= Key('SK').between(
                    f'SIGNAL#{start_time.isoformat()}',
                    f'SIGNAL#{end_time.isoformat()}'
                )
            elif start_time:
                key_condition &= Key('SK').gte(f'SIGNAL#{start_time.isoformat()}')
            elif end_time:
                key_condition &= Key('SK').lte(f'SIGNAL#{end_time.isoformat()}')
            else:
                # Query all signals for the team
                key_condition &= Key('SK').begins_with('SIGNAL#')
            
            query_params = {
                'KeyConditionExpression': key_condition,
                'ScanIndexForward': False  # Most recent first
            }
            
            if limit:
                query_params['Limit'] = limit
            
            response = self.team_signals_table.query(**query_params)
            return response.get('Items', [])
            
        except ClientError as e:
            raise ClientError(
                error_response={
                    'Error': {
                        'Code': e.response['Error']['Code'],
                        'Message': f"Failed to query team signals: {e.response['Error']['Message']}"
                    }
                },
                operation_name='Query'
            )
    
    def scan_team_signals(
        self,
        filter_expression: Optional[Any] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan all team signals with optional filtering.
        
        Args:
            filter_expression: Optional boto3 filter expression
            limit: Maximum number of items to return (optional)
            
        Returns:
            List of team signal items
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        try:
            scan_params = {}
            
            if filter_expression:
                scan_params['FilterExpression'] = filter_expression
            
            if limit:
                scan_params['Limit'] = limit
            
            response = self.team_signals_table.scan(**scan_params)
            items = response.get('Items', [])
            
            # Handle pagination if needed
            while 'LastEvaluatedKey' in response and (not limit or len(items) < limit):
                scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = self.team_signals_table.scan(**scan_params)
                items.extend(response.get('Items', []))
            
            return items[:limit] if limit else items
            
        except ClientError as e:
            raise ClientError(
                error_response={
                    'Error': {
                        'Code': e.response['Error']['Code'],
                        'Message': f"Failed to scan team signals: {e.response['Error']['Message']}"
                    }
                },
                operation_name='Scan'
            )
    
    # RiskRecords table operations
    
    def put_risk_record(self, risk_record: RiskRecord) -> Dict[str, Any]:
        """
        Store a risk record in DynamoDB with TTL for 90-day retention.
        
        Args:
            risk_record: RiskRecord instance to store
            
        Returns:
            Response from DynamoDB put operation
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        item = risk_record.to_dynamodb_item()
        
        # Add TTL for 90-day retention
        ttl_timestamp = int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())
        item['ttl'] = ttl_timestamp
        
        # Convert floats to Decimal for DynamoDB
        item = self._convert_floats_to_decimal(item)
        
        try:
            response = self.risk_records_table.put_item(Item=item)
            return response
        except ClientError as e:
            raise ClientError(
                error_response={
                    'Error': {
                        'Code': e.response['Error']['Code'],
                        'Message': f"Failed to store risk record: {e.response['Error']['Message']}"
                    }
                },
                operation_name='PutItem'
            )
    
    def query_risk_records(
        self,
        team_id: str,
        analysis_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query risk records for a specific team and optionally a specific analysis.
        
        Args:
            team_id: Team identifier
            analysis_id: Analysis identifier (optional)
            limit: Maximum number of items to return (optional)
            
        Returns:
            List of risk record items
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        try:
            key_condition = Key('PK').eq(f'TEAM#{team_id}')
            
            if analysis_id:
                # Query for specific analysis
                key_condition &= Key('SK').begins_with(f'RISK#{analysis_id}#')
            else:
                # Query all risks for the team
                key_condition &= Key('SK').begins_with('RISK#')
            
            query_params = {
                'KeyConditionExpression': key_condition,
                'ScanIndexForward': False  # Most recent first
            }
            
            if limit:
                query_params['Limit'] = limit
            
            response = self.risk_records_table.query(**query_params)
            return response.get('Items', [])
            
        except ClientError as e:
            raise ClientError(
                error_response={
                    'Error': {
                        'Code': e.response['Error']['Code'],
                        'Message': f"Failed to query risk records: {e.response['Error']['Message']}"
                    }
                },
                operation_name='Query'
            )
    
    def get_risk_record(
        self,
        team_id: str,
        analysis_id: str,
        risk_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific risk record by its identifiers.
        
        Args:
            team_id: Team identifier
            analysis_id: Analysis identifier
            risk_id: Risk identifier
            
        Returns:
            Risk record item or None if not found
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        try:
            response = self.risk_records_table.get_item(
                Key={
                    'PK': f'TEAM#{team_id}',
                    'SK': f'RISK#{analysis_id}#{risk_id}'
                }
            )
            return response.get('Item')
            
        except ClientError as e:
            raise ClientError(
                error_response={
                    'Error': {
                        'Code': e.response['Error']['Code'],
                        'Message': f"Failed to get risk record: {e.response['Error']['Message']}"
                    }
                },
                operation_name='GetItem'
            )
    
    # Utility methods
    
    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """
        Recursively convert float values to Decimal for DynamoDB compatibility.
        
        Args:
            obj: Object to convert (dict, list, or primitive)
            
        Returns:
            Object with floats converted to Decimal
        """
        if isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        elif isinstance(obj, float):
            return Decimal(str(obj))
        else:
            return obj
