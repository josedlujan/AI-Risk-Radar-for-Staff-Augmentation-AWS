"""Unit tests for MockDataGenerator."""

import pytest
from backend.mock_data.mock_data_generator import MockDataGenerator
from backend.models.risk_record import SeverityLevel


class TestMockDataGenerator:
    """Test suite for MockDataGenerator class."""
    
    def test_generate_team_signals_returns_five_dimensions(self):
        """Test that generated signals contain all five risk dimensions."""
        generator = MockDataGenerator(seed=42)
        signals = generator.generate_team_signals()
        
        assert "delivery_cadence" in signals
        assert "knowledge_concentration" in signals
        assert "dependency_risk" in signals
        assert "workload_distribution" in signals
        assert "attrition_signal" in signals
        assert len(signals) == 5
    
    def test_generate_team_signals_values_in_valid_range(self):
        """Test that all signal values are within 0-100 range."""
        generator = MockDataGenerator(seed=42)
        signals = generator.generate_team_signals()
        
        for dimension, value in signals.items():
            assert 0 <= value <= 100, f"{dimension} value {value} out of range"
    
    def test_generate_team_signals_with_custom_team_size(self):
        """Test signal generation with custom team size."""
        generator = MockDataGenerator(seed=42)
        
        # Generate multiple samples to check the trend
        small_samples = [generator.generate_team_signals(team_size=3) for _ in range(5)]
        
        generator = MockDataGenerator(seed=42)  # Reset seed
        large_samples = [generator.generate_team_signals(team_size=20) for _ in range(5)]
        
        # Calculate average knowledge concentration
        avg_small = sum(s["knowledge_concentration"] for s in small_samples) / len(small_samples)
        avg_large = sum(s["knowledge_concentration"] for s in large_samples) / len(large_samples)
        
        # Small teams should have higher average knowledge concentration risk
        assert avg_small > avg_large, f"Expected small teams ({avg_small}) to have higher knowledge concentration than large teams ({avg_large})"
    
    def test_generate_team_signals_with_many_projects(self):
        """Test that many projects increase workload and dependency risk."""
        generator = MockDataGenerator(seed=42)
        signals_few = generator.generate_team_signals(team_size=8, project_count=2)
        signals_many = generator.generate_team_signals(team_size=8, project_count=6)
        
        # Many projects should increase workload and dependency risk
        assert signals_many["workload_distribution"] > signals_few["workload_distribution"]
        assert signals_many["dependency_risk"] > signals_few["dependency_risk"]
    
    def test_generate_healthy_scenario(self):
        """Test healthy scenario generation."""
        generator = MockDataGenerator(seed=42)
        result = generator.generate_risk_scenario("healthy")
        
        assert result["scenario"] == "healthy"
        assert result["is_mock"] is True
        assert result["team_signal"] is not None
        assert len(result["risks"]) == 4  # One per severity level
        
        # Check all signal values are relatively low (healthy)
        signals = result["team_signal"]
        assert signals.delivery_cadence < 40
        assert signals.knowledge_concentration < 40
        assert signals.dependency_risk < 40
        assert signals.workload_distribution < 40
        assert signals.attrition_signal < 40
    
    def test_generate_overloaded_scenario(self):
        """Test overloaded scenario generation."""
        generator = MockDataGenerator(seed=42)
        result = generator.generate_risk_scenario("overloaded")
        
        assert result["scenario"] == "overloaded"
        assert len(result["risks"]) == 5  # Updated to 5 risks
        
        # Check high workload and attrition signals
        signals = result["team_signal"]
        assert signals.workload_distribution > 70
        assert signals.attrition_signal > 60
        
        # Verify critical severity risk exists
        severities = [risk.severity for risk in result["risks"]]
        assert SeverityLevel.CRITICAL in severities
    
    def test_generate_knowledge_silo_scenario(self):
        """Test knowledge silo scenario generation."""
        generator = MockDataGenerator(seed=42)
        result = generator.generate_risk_scenario("knowledge_silo")
        
        assert result["scenario"] == "knowledge_silo"
        assert len(result["risks"]) == 4
        
        # Check high knowledge concentration
        signals = result["team_signal"]
        assert signals.knowledge_concentration > 80
        
        # Verify knowledge_concentration dimension has critical risk
        knowledge_risks = [r for r in result["risks"] if r.dimension == "knowledge_concentration"]
        assert len(knowledge_risks) > 0
        assert any(r.severity == SeverityLevel.CRITICAL for r in knowledge_risks)
    
    def test_generate_dependency_heavy_scenario(self):
        """Test dependency-heavy scenario generation."""
        generator = MockDataGenerator(seed=42)
        result = generator.generate_risk_scenario("dependency_heavy")
        
        assert result["scenario"] == "dependency_heavy"
        assert len(result["risks"]) == 4
        
        # Check high dependency risk
        signals = result["team_signal"]
        assert signals.dependency_risk > 75
        
        # Verify dependency_risk dimension has critical risk
        dependency_risks = [r for r in result["risks"] if r.dimension == "dependency_risk"]
        assert len(dependency_risks) > 0
        assert any(r.severity == SeverityLevel.CRITICAL for r in dependency_risks)
    
    def test_generate_attrition_warning_scenario(self):
        """Test attrition warning scenario generation."""
        generator = MockDataGenerator(seed=42)
        result = generator.generate_risk_scenario("attrition_warning")
        
        assert result["scenario"] == "attrition_warning"
        assert len(result["risks"]) == 4
        
        # Check high attrition signal
        signals = result["team_signal"]
        assert signals.attrition_signal > 85
        
        # Verify attrition_signal dimension has critical risk
        attrition_risks = [r for r in result["risks"] if r.dimension == "attrition_signal"]
        assert len(attrition_risks) > 0
        assert any(r.severity == SeverityLevel.CRITICAL for r in attrition_risks)
    
    def test_all_scenarios_have_four_severity_levels(self):
        """Test that each scenario includes at least one risk per severity level."""
        generator = MockDataGenerator(seed=42)
        scenarios = ["healthy", "overloaded", "knowledge_silo", "dependency_heavy", "attrition_warning"]
        
        for scenario in scenarios:
            result = generator.generate_risk_scenario(scenario)
            severities = {risk.severity for risk in result["risks"]}
            
            # Each scenario should have all four severity levels
            assert SeverityLevel.CRITICAL in severities, f"{scenario} missing CRITICAL"
            assert SeverityLevel.HIGH in severities, f"{scenario} missing HIGH"
            assert SeverityLevel.MEDIUM in severities, f"{scenario} missing MEDIUM"
            assert SeverityLevel.LOW in severities, f"{scenario} missing LOW"
    
    def test_all_risks_have_bilingual_content(self):
        """Test that all generated risks have both English and Spanish content."""
        generator = MockDataGenerator(seed=42)
        result = generator.generate_risk_scenario("overloaded")
        
        for risk in result["risks"]:
            assert risk.description_en, f"Risk {risk.risk_id} missing English description"
            assert risk.description_es, f"Risk {risk.risk_id} missing Spanish description"
            assert len(risk.recommendations_en) > 0, f"Risk {risk.risk_id} missing English recommendations"
            assert len(risk.recommendations_es) > 0, f"Risk {risk.risk_id} missing Spanish recommendations"
            assert len(risk.recommendations_en) == len(risk.recommendations_es), \
                f"Risk {risk.risk_id} has mismatched recommendation counts"
    
    def test_all_risks_have_minimum_one_recommendation(self):
        """Test that all risks have at least one recommendation in each language."""
        generator = MockDataGenerator(seed=42)
        scenarios = ["healthy", "overloaded", "knowledge_silo", "dependency_heavy", "attrition_warning"]
        
        for scenario in scenarios:
            result = generator.generate_risk_scenario(scenario)
            for risk in result["risks"]:
                assert len(risk.recommendations_en) >= 1, \
                    f"{scenario} risk {risk.dimension} has no English recommendations"
                assert len(risk.recommendations_es) >= 1, \
                    f"{scenario} risk {risk.dimension} has no Spanish recommendations"
    
    def test_team_signal_has_correct_metadata(self):
        """Test that generated team signals have correct metadata."""
        generator = MockDataGenerator(seed=42)
        result = generator.generate_risk_scenario("healthy", team_size=10, project_count=5)
        
        signal = result["team_signal"]
        assert signal.metadata.team_size == 10
        assert signal.metadata.project_count == 5
        assert signal.metadata.aggregation_period == "weekly"
    
    def test_invalid_scenario_raises_error(self):
        """Test that invalid scenario name raises ValueError."""
        generator = MockDataGenerator(seed=42)
        
        with pytest.raises(ValueError, match="Unknown scenario"):
            generator.generate_risk_scenario("invalid_scenario")
    
    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results for scenarios."""
        gen1 = MockDataGenerator(seed=123)
        gen2 = MockDataGenerator(seed=123)
        
        result1 = gen1.generate_risk_scenario("healthy")
        result2 = gen2.generate_risk_scenario("healthy")
        
        # Compare signal values
        assert result1["team_signal"].delivery_cadence == result2["team_signal"].delivery_cadence
        assert result1["team_signal"].knowledge_concentration == result2["team_signal"].knowledge_concentration
        assert result1["team_signal"].dependency_risk == result2["team_signal"].dependency_risk
        assert result1["team_signal"].workload_distribution == result2["team_signal"].workload_distribution
        assert result1["team_signal"].attrition_signal == result2["team_signal"].attrition_signal
    
    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different results for random signal generation."""
        gen1 = MockDataGenerator(seed=123)
        gen2 = MockDataGenerator(seed=456)
        
        # Use generate_team_signals which has randomness
        signals1 = gen1.generate_team_signals()
        signals2 = gen2.generate_team_signals()
        
        # At least one signal should be different
        signals_different = (
            signals1["delivery_cadence"] != signals2["delivery_cadence"] or
            signals1["knowledge_concentration"] != signals2["knowledge_concentration"] or
            signals1["dependency_risk"] != signals2["dependency_risk"] or
            signals1["workload_distribution"] != signals2["workload_distribution"] or
            signals1["attrition_signal"] != signals2["attrition_signal"]
        )
        assert signals_different, "Different seeds should produce different random signals"
    
    def test_risk_signal_values_match_scenario_signals(self):
        """Test that risk records contain the correct signal values."""
        generator = MockDataGenerator(seed=42)
        result = generator.generate_risk_scenario("overloaded")
        
        expected_signals = {
            "delivery_cadence": result["team_signal"].delivery_cadence,
            "knowledge_concentration": result["team_signal"].knowledge_concentration,
            "dependency_risk": result["team_signal"].dependency_risk,
            "workload_distribution": result["team_signal"].workload_distribution,
            "attrition_signal": result["team_signal"].attrition_signal
        }
        
        for risk in result["risks"]:
            assert risk.signal_values == expected_signals
