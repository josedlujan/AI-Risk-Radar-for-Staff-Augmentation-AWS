"""Bedrock integration for AI-powered team risk analysis."""

import json
import time
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

from models import AnalysisResult, RiskRecord, SeverityLevel


class BedrockAnalyzer:
    """Analyzes team signals using Amazon Bedrock Claude 3.5 Sonnet."""
    
    MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0  # seconds
    
    def __init__(self, region_name: str = "us-east-1"):
        """Initialize Bedrock client.
        
        Args:
            region_name: AWS region for Bedrock service
        """
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
    
    def analyze_team_signals(
        self,
        team_id: str,
        signals: Dict[str, float],
        metadata: Dict[str, Any]
    ) -> AnalysisResult:
        """Analyze team signals and identify risks with bilingual recommendations.
        
        Args:
            team_id: Team identifier
            signals: Dictionary with five risk dimension values
            metadata: Team metadata (team_size, project_count, etc.)
        
        Returns:
            AnalysisResult with identified risks and recommendations
        
        Raises:
            ValueError: If signals are invalid
            RuntimeError: If Bedrock API fails after retries
        """
        start_time = time.time()
        
        # Construct prompt for Claude
        prompt = self._construct_prompt(signals, metadata)
        
        # Invoke Bedrock with retry logic
        response_text = self._invoke_bedrock_with_retry(prompt)
        
        # Parse response
        analysis_result = self._parse_response(team_id, response_text)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        analysis_result.analysis_duration_ms = duration_ms
        
        return analysis_result
    
    def _construct_prompt(
        self,
        signals: Dict[str, float],
        metadata: Dict[str, Any]
    ) -> str:
        """Construct analysis prompt for Claude 3.5 Sonnet.
        
        Args:
            signals: Five risk dimension values
            metadata: Team metadata
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert engineering team health analyst. Analyze the following aggregated team-level signals and identify risks across five dimensions.

Team Metadata:
- Team Size: {metadata.get('team_size', 'unknown')} engineers
- Project Count: {metadata.get('project_count', 'unknown')} projects
- Aggregation Period: {metadata.get('aggregation_period', 'unknown')}

Risk Dimension Signals (0-100 scale, higher = more risk):
- Delivery Cadence: {signals.get('delivery_cadence', 0):.1f}
- Knowledge Concentration: {signals.get('knowledge_concentration', 0):.1f}
- Dependency Risk: {signals.get('dependency_risk', 0):.1f}
- Workload Distribution: {signals.get('workload_distribution', 0):.1f}
- Attrition Signal: {signals.get('attrition_signal', 0):.1f}

Instructions:
1. Analyze each dimension and identify risks based on the signal values
2. Classify each risk as: critical (>80), high (60-80), medium (40-60), or low (<40)
3. Provide actionable recommendations for each identified risk
4. Output MUST be in BOTH Spanish and English
5. Focus on team-level insights only (never mention individual engineers)

Output Format (JSON):
{{
  "risks": [
    {{
      "dimension": "dimension_name",
      "severity": "critical|high|medium|low",
      "description_en": "English description of the risk",
      "description_es": "Spanish description of the risk",
      "recommendations_en": ["English recommendation 1", "English recommendation 2"],
      "recommendations_es": ["Spanish recommendation 1", "Spanish recommendation 2"]
    }}
  ]
}}

Provide your analysis as valid JSON only, no additional text."""
        
        return prompt
    
    def _invoke_bedrock_with_retry(self, prompt: str) -> str:
        """Invoke Bedrock API with exponential backoff retry logic.
        
        Args:
            prompt: Analysis prompt
        
        Returns:
            Response text from Claude
        
        Raises:
            RuntimeError: If all retries fail
        """
        backoff = self.INITIAL_BACKOFF
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Construct request body for Claude 3.5 Sonnet
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4096,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,  # Lower temperature for more consistent analysis
                }
                
                # Invoke Bedrock
                response = self.client.invoke_model(
                    modelId=self.MODEL_ID,
                    body=json.dumps(request_body),
                    contentType="application/json",
                    accept="application/json"
                )
                
                # Parse response
                response_body = json.loads(response["body"].read())
                
                # Extract text from Claude's response
                if "content" in response_body and len(response_body["content"]) > 0:
                    return response_body["content"][0]["text"]
                else:
                    raise ValueError("Invalid response format from Bedrock")
                
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                last_error = e
                
                # Handle throttling with retry
                if error_code in ["ThrottlingException", "TooManyRequestsException"]:
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(backoff)
                        backoff *= 2  # Exponential backoff
                        continue
                    else:
                        # Max retries reached for throttling
                        last_error = e
                        break
                
                # Handle timeout with retry
                elif error_code in ["TimeoutError", "RequestTimeout"]:
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    else:
                        # Max retries reached for timeout
                        last_error = e
                        break
                
                # Other errors - don't retry
                raise RuntimeError(f"Bedrock API error: {error_code} - {str(e)}")
            
            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise RuntimeError(f"Unexpected error invoking Bedrock: {str(e)}")
        
        # All retries exhausted
        raise RuntimeError(f"Bedrock API failed after {self.MAX_RETRIES} retries: {str(last_error)}")
    
    def _parse_response(self, team_id: str, response_text: str) -> AnalysisResult:
        """Parse Bedrock response into AnalysisResult.
        
        Args:
            team_id: Team identifier
            response_text: JSON response from Claude
        
        Returns:
            AnalysisResult with parsed risks
        
        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Extract JSON from response (Claude might include markdown code blocks)
            json_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            
            json_text = json_text.strip()
            
            # Parse JSON
            data = json.loads(json_text)
            
            if "risks" not in data:
                raise ValueError("Response missing 'risks' field")
            
            # Create AnalysisResult
            analysis_result = AnalysisResult(team_id=team_id)
            
            # Parse each risk
            for risk_data in data["risks"]:
                # Validate required fields
                required_fields = [
                    "dimension", "severity", "description_en", "description_es",
                    "recommendations_en", "recommendations_es"
                ]
                for field in required_fields:
                    if field not in risk_data:
                        raise ValueError(f"Risk missing required field: {field}")
                
                # Validate severity
                severity_str = risk_data["severity"].lower()
                try:
                    severity = SeverityLevel(severity_str)
                except ValueError:
                    raise ValueError(f"Invalid severity level: {severity_str}")
                
                # Validate recommendations are non-empty
                if not risk_data["recommendations_en"] or not risk_data["recommendations_es"]:
                    raise ValueError("Recommendations cannot be empty")
                
                # Create RiskRecord
                risk_record = RiskRecord(
                    analysis_id=analysis_result.analysis_id,
                    team_id=team_id,
                    dimension=risk_data["dimension"],
                    severity=severity,
                    description_en=risk_data["description_en"],
                    description_es=risk_data["description_es"],
                    recommendations_en=risk_data["recommendations_en"],
                    recommendations_es=risk_data["recommendations_es"],
                    signal_values={}  # Will be populated by caller
                )
                
                analysis_result.risks.append(risk_record)
            
            return analysis_result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Bedrock response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing Bedrock response: {str(e)}")
