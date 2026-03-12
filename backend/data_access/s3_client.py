"""S3 client wrapper for snapshot storage and retrieval."""

import os
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from models.snapshot import Snapshot


class S3Client:
    """Wrapper for S3 operations on historical snapshots."""
    
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region_name: str = "us-east-1"
    ):
        """
        Initialize S3 client.
        
        Args:
            bucket_name: Name of S3 bucket for snapshots (defaults to env var)
            region_name: AWS region name
        """
        self.s3_client = boto3.client('s3', region_name=region_name)
        
        self.bucket_name = bucket_name or os.environ.get(
            'SNAPSHOTS_BUCKET', 'team-risk-snapshots'
        )
    
    def put_snapshot(self, snapshot: Snapshot) -> dict:
        """
        Store a snapshot in S3 with timestamp-based key.
        
        Args:
            snapshot: Snapshot instance to store
            
        Returns:
            Response from S3 put operation with 'key' and 'bucket' fields
            
        Raises:
            ClientError: If S3 operation fails
        """
        key = snapshot.get_s3_key()
        json_content = snapshot.to_json()
        
        try:
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_content.encode('utf-8'),
                ContentType='application/json'
            )
            
            return {
                'key': key,
                'bucket': self.bucket_name,
                'etag': response.get('ETag'),
                'version_id': response.get('VersionId')
            }
            
        except ClientError as e:
            raise ClientError(
                error_response={
                    'Error': {
                        'Code': e.response['Error']['Code'],
                        'Message': f"Failed to store snapshot: {e.response['Error']['Message']}"
                    }
                },
                operation_name='PutObject'
            )
    
    def get_snapshot(self, key: str) -> Snapshot:
        """
        Retrieve and parse a snapshot from S3.
        
        Args:
            key: S3 key for the snapshot
            
        Returns:
            Parsed Snapshot instance
            
        Raises:
            ClientError: If S3 operation fails or snapshot not found
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            json_content = response['Body'].read().decode('utf-8')
            return Snapshot.from_json(json_content)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise ClientError(
                    error_response={
                        'Error': {
                            'Code': 'NoSuchKey',
                            'Message': f"Snapshot not found: {key}"
                        }
                    },
                    operation_name='GetObject'
                )
            else:
                raise ClientError(
                    error_response={
                        'Error': {
                            'Code': e.response['Error']['Code'],
                            'Message': f"Failed to retrieve snapshot: {e.response['Error']['Message']}"
                        }
                    },
                    operation_name='GetObject'
                )
    
    def get_snapshot_by_team_and_timestamp(
        self,
        team_id: str,
        timestamp_iso: str
    ) -> Snapshot:
        """
        Retrieve a snapshot by team ID and ISO timestamp.
        
        Args:
            team_id: Team identifier
            timestamp_iso: ISO format timestamp (e.g., "2024-01-15T10:30:00")
            
        Returns:
            Parsed Snapshot instance
            
        Raises:
            ClientError: If S3 operation fails or snapshot not found
        """
        # Parse timestamp to construct key
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp_iso)
        key = f"snapshots/{team_id}/{dt.year}/{dt.month:02d}/{dt.day:02d}/{timestamp_iso}.json"
        
        return self.get_snapshot(key)
    
    def list_snapshots(
        self,
        team_id: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000
    ) -> list[dict]:
        """
        List snapshots for a team with optional prefix filtering.
        
        Args:
            team_id: Team identifier
            prefix: Optional additional prefix (e.g., "2024/01" for January 2024)
            max_keys: Maximum number of keys to return
            
        Returns:
            List of snapshot metadata dictionaries with 'key', 'size', and 'last_modified'
            
        Raises:
            ClientError: If S3 operation fails
        """
        base_prefix = f"snapshots/{team_id}/"
        if prefix:
            list_prefix = f"{base_prefix}{prefix}"
        else:
            list_prefix = base_prefix
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=list_prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' not in response:
                return []
            
            return [
                {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                }
                for obj in response['Contents']
            ]
            
        except ClientError as e:
            raise ClientError(
                error_response={
                    'Error': {
                        'Code': e.response['Error']['Code'],
                        'Message': f"Failed to list snapshots: {e.response['Error']['Message']}"
                    }
                },
                operation_name='ListObjectsV2'
            )
    
    def delete_snapshot(self, key: str) -> dict:
        """
        Delete a snapshot from S3.
        
        Args:
            key: S3 key for the snapshot to delete
            
        Returns:
            Response from S3 delete operation
            
        Raises:
            ClientError: If S3 operation fails
        """
        try:
            response = self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            return {
                'key': key,
                'bucket': self.bucket_name,
                'deleted': True
            }
            
        except ClientError as e:
            raise ClientError(
                error_response={
                    'Error': {
                        'Code': e.response['Error']['Code'],
                        'Message': f"Failed to delete snapshot: {e.response['Error']['Message']}"
                    }
                },
                operation_name='DeleteObject'
            )
