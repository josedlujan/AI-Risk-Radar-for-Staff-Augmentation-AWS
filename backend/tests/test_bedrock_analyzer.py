"""Unit tests for BedrockAnalyzer class."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from backend.ai.bedrock_analyzer import BedrockAnalyzer
from backend.models import AnalysisResult, SeverityLevel


class TestBedrockAnalyzer:
    """Test suite for BedrockAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create BedrockAnalyzer instance with mocked boto3 client."""
        with patch('boto3.client'):
            return BedrockAnalyzer(region_name="us-east-1")
    
    @pytest.fixture
    def sample_signals(self):
        """Sample team signals."""
        return {
            "delivery_cadence": 75.0,
            "knowledge_concentration": 85.0,
            "dependency_risk": 45.0,
            "workload_distribution": 60.0,
            "attrition_signal": 30.0
        }
    
    @pytest.fixture
    def sample_metadata(self):
        """Sample team metadata."""
        return {
            "team_size": 8,
            "project_count": 3,
            "aggregation_period": "weekly"
        }
    
    @pytest.fixture
    def sample_bedrock_response(self):
        """Sample valid Bedrock response."""
        return {
            "risks": [
                {
                    "dimension": "knowledge_concentration",
                    "severity": "critical",
                    "description_en": "High knowledge concentration detected",
                    "description_es": "Alta concentración de conocimiento detectada",
                    "recommendations_en": ["Implement knowledge sharing sessions"],
                    "recommendations_es": ["Implementar sesiones de intercambio de conocimiento"]
                },
                {
                    "dimension": "delivery_cadence",
                    "severity": "high",
                    "description_en": "Delivery pace is slowing",
                    "description_es": "El ritmo de entrega está disminuyendo",
                    "recommendations_en": ["Review sprint planning process"],
                    "recommendations_es": ["Revisar el proceso de planificación de sprints"]
                }
            ]
        }
    
    def test_construct_prompt(self, analyzer, sample_signals, sample_metadata):
        """Test prompt construction includes all required elements."""
        prompt = analyzer._construct_prompt(sample_signals, sample_metadata)
        
        # Check metadata is included
        assert "Team Size: 8" in prompt
        assert "Project Count: 3" in prompt
        assert "Aggregation Period: weekly" in prompt
        
        # Check all five dimensions are included
        assert "Delivery Cadence: 75.0" in prompt
        assert "Knowledge Concentration: 85.0" in prompt
        assert "Dependency Risk: 45.0" in prompt
        assert "Workload Distribution: 60.0" in prompt
        assert "Attrition Signal: 30.0" in prompt
        
        # Check bilingual requirement
        assert "Spanish and English" in prompt or "BOTH Spanish and English" in prompt
        
        # Check JSON format requirement
        assert "JSON" in prompt
    
    def test_parse_response_valid(self, analyzer, sample_bedrock_response):
        """Test parsing valid Bedrock response."""
        response_text = json.dumps(sample_bedrock_response)
        result = analyzer._parse_response("team-123", response_text)
        
        assert isinstance(result, AnalysisResult)
        assert result.team_id == "team-123"
        assert len(result.risks) == 2
        
        # Check first risk
        risk1 = result.risks[0]
        assert risk1.dimension == "knowledge_concentration"
        assert risk1.severity == SeverityLevel.CRITICAL
        assert risk1.description_en == "High knowledge concentration detected"
        assert risk1.description_es == "Alta concentración de conocimiento detectada"
        assert len(risk1.recommendations_en) == 1
        assert len(risk1.recommendations_es) == 1
        
        # Check second risk
        risk2 = result.risks[1]
        assert risk2.severity == SeverityLevel.HIGH
    
    def test_parse_response_with_markdown_code_blocks(self, analyzer, sample_bedrock_response):
        """Test parsing response wrapped in markdown code blocks."""
        response_text = f"```json\n{json.dumps(sample_bedrock_response)}\n```"
        result = analyzer._parse_response("team-123", response_text)
        
        assert isinstance(result, AnalysisResult)
        assert len(result.risks) == 2
    
    def test_parse_response_missing_risks_field(self, analyzer):
        """Test parsing response without 'risks' field."""
        response_text = json.dumps({"data": []})
        
        with pytest.raises(ValueError, match="missing 'risks' field"):
            analyzer._parse_response("team-123", response_text)
    
    def test_parse_response_invalid_json(self, analyzer):
        """Test parsing invalid JSON."""
        response_text = "This is not JSON"
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            analyzer._parse_response("team-123", response_text)
    
    def test_parse_response_missing_required_field(self, analyzer):
        """Test parsing response with missing required field."""
        response_data = {
            "risks": [
                {
                    "dimension": "delivery_cadence",
                    "severity": "high",
                    # Missing description_en, description_es, recommendations
                }
            ]
        }
        response_text = json.dumps(response_data)
        
        with pytest.raises(ValueError, match="missing required field"):
            analyzer._parse_response("team-123", response_text)
    
    def test_parse_response_invalid_severity(self, analyzer):
        """Test parsing response with invalid severity level."""
        response_data = {
            "risks": [
                {
                    "dimension": "delivery_cadence",
                    "severity": "super_critical",  # Invalid
                    "description_en": "Test",
                    "description_es": "Prueba",
                    "recommendations_en": ["Fix it"],
                    "recommendations_es": ["Arreglarlo"]
                }
            ]
        }
        response_text = json.dumps(response_data)
        
        with pytest.raises(ValueError, match="Invalid severity level"):
            analyzer._parse_response("team-123", response_text)
    
    def test_parse_response_empty_recommendations(self, analyzer):
        """Test parsing response with empty recommendations."""
        response_data = {
            "risks": [
                {
                    "dimension": "delivery_cadence",
                    "severity": "high",
                    "description_en": "Test",
                    "description_es": "Prueba",
                    "recommendations_en": [],  # Empty
                    "recommendations_es": []   # Empty
                }
            ]
        }
        response_text = json.dumps(response_data)
        
        with pytest.raises(ValueError, match="Recommendations cannot be empty"):
            analyzer._parse_response("team-123", response_text)
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_invoke_bedrock_with_retry_success(self, mock_sleep, analyzer, sample_bedrock_response):
        """Test successful Bedrock invocation."""
        # Mock successful response
        mock_response = {
            "body": MagicMock()
        }
        response_body = {
            "content": [
                {"text": json.dumps(sample_bedrock_response)}
            ]
        }
        mock_response["body"].read.return_value = json.dumps(response_body).encode()
        
        analyzer.client.invoke_model = Mock(return_value=mock_response)
        
        result = analyzer._invoke_bedrock_with_retry("test prompt")
        
        assert result == json.dumps(sample_bedrock_response)
        analyzer.client.invoke_model.assert_called_once()
    
    @patch('time.sleep')
    def test_invoke_bedrock_with_retry_throttling(self, mock_sleep, analyzer, sample_bedrock_response):
        """Test retry logic on throttling error."""
        # First two calls fail with throttling, third succeeds
        mock_response = {
            "body": MagicMock()
        }
        response_body = {
            "content": [
                {"text": json.dumps(sample_bedrock_response)}
            ]
        }
        mock_response["body"].read.return_value = json.dumps(response_body).encode()
        
        throttle_error = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "InvokeModel"
        )
        
        analyzer.client.invoke_model = Mock(
            side_effect=[throttle_error, throttle_error, mock_response]
        )
        
        result = analyzer._invoke_bedrock_with_retry("test prompt")
        
        assert result == json.dumps(sample_bedrock_response)
        assert analyzer.client.invoke_model.call_count == 3
        assert mock_sleep.call_count == 2  # Two retries
    
    @patch('time.sleep')
    def test_invoke_bedrock_with_retry_max_retries_exceeded(self, mock_sleep, analyzer):
        """Test failure after max retries."""
        throttle_error = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "InvokeModel"
        )
        
        analyzer.client.invoke_model = Mock(side_effect=throttle_error)
        
        with pytest.raises(RuntimeError, match="failed after 3 retries"):
            analyzer._invoke_bedrock_with_retry("test prompt")
        
        assert analyzer.client.invoke_model.call_count == 3
    
    @patch('time.sleep')
    def test_invoke_bedrock_with_retry_non_retryable_error(self, mock_sleep, analyzer):
        """Test immediate failure on non-retryable error."""
        access_error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
            "InvokeModel"
        )
        
        analyzer.client.invoke_model = Mock(side_effect=access_error)
        
        with pytest.raises(RuntimeError, match="Bedrock API error"):
            analyzer._invoke_bedrock_with_retry("test prompt")
        
        # Should not retry on access errors
        assert analyzer.client.invoke_model.call_count == 1
    
    def test_analyze_team_signals_integration(self, analyzer, sample_signals, sample_metadata, sample_bedrock_response):
        """Test full analyze_team_signals flow."""
        # Mock Bedrock response
        mock_response = {
            "body": MagicMock()
        }
        response_body = {
            "content": [
                {"text": json.dumps(sample_bedrock_response)}
            ]
        }
        mock_response["body"].read.return_value = json.dumps(response_body).encode()
        
        analyzer.client.invoke_model = Mock(return_value=mock_response)
        
        # Mock time to ensure duration is calculated
        with patch('time.time', side_effect=[0.0, 0.5]):  # 500ms duration
            result = analyzer.analyze_team_signals("team-123", sample_signals, sample_metadata)
        
        assert isinstance(result, AnalysisResult)
        assert result.team_id == "team-123"
        assert len(result.risks) == 2
        assert result.analysis_duration_ms == 500
        
        # Verify Bedrock was called
        analyzer.client.invoke_model.assert_called_once()
        call_args = analyzer.client.invoke_model.call_args
        assert call_args[1]["modelId"] == BedrockAnalyzer.MODEL_ID
    
    def test_exponential_backoff_timing(self, analyzer):
        """Test that backoff increases exponentially."""
        with patch('time.sleep') as mock_sleep:
            throttle_error = ClientError(
                {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
                "InvokeModel"
            )
            analyzer.client.invoke_model = Mock(side_effect=throttle_error)
            
            try:
                analyzer._invoke_bedrock_with_retry("test prompt")
            except RuntimeError:
                pass
            
            # Check backoff times: 1.0, 2.0
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert sleep_calls[0] == 1.0
            assert sleep_calls[1] == 2.0
