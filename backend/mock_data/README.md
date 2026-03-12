# MockDataGenerator Usage Guide

The `MockDataGenerator` class creates realistic team signals and risk scenarios for demonstration and testing purposes.

## Features

- Generates realistic team signals for 8 engineers across 3 projects (configurable)
- Creates signals with controlled variance across five risk dimensions
- Provides predefined risk scenarios with bilingual recommendations
- Ensures at least one risk per severity level (critical, high, medium, low)

## Quick Start

```python
from backend.mock_data import MockDataGenerator

# Create generator
generator = MockDataGenerator(seed=42)  # Optional seed for reproducibility

# Generate random team signals
signals = generator.generate_team_signals(
    team_size=8,
    project_count=3,
    team_id="demo-team-001"
)
# Returns: Dict with five dimensions (0-100 scale)
```

## Predefined Scenarios

### 1. Healthy Team
Low risk across all dimensions with balanced workload.

```python
result = generator.generate_risk_scenario("healthy")
```

### 2. Overloaded Team
High workload, delivery delays, and attrition risk.

```python
result = generator.generate_risk_scenario("overloaded")
```

### 3. Knowledge Silo
Critical knowledge concentration with few experts.

```python
result = generator.generate_risk_scenario("knowledge_silo")
```

### 4. Dependency Heavy
Critical external dependencies blocking progress.

```python
result = generator.generate_risk_scenario("dependency_heavy")
```

### 5. Attrition Warning
Critical attrition indicators requiring immediate action.

```python
result = generator.generate_risk_scenario("attrition_warning")
```

## Scenario Output Structure

Each scenario returns:

```python
{
    "team_signal": TeamSignal,  # Pydantic model with five dimensions
    "risks": List[RiskRecord],  # 4-5 risks with bilingual recommendations
    "scenario": str,            # Scenario name
    "is_mock": True            # Mock data indicator
}
```

## Risk Dimensions

All scenarios include these five dimensions (0-100 scale, higher = more risk):

1. **Delivery Cadence**: Sprint velocity and delivery consistency
2. **Knowledge Concentration**: Expertise distribution across team
3. **Dependency Risk**: External blockers and dependencies
4. **Workload Distribution**: Task balance across team members
5. **Attrition Signal**: Team member retention indicators

## Bilingual Support

All risk descriptions and recommendations are provided in:
- English (`description_en`, `recommendations_en`)
- Spanish (`description_es`, `recommendations_es`)

## Testing

Run the test suite:

```bash
python3 -m pytest backend/tests/test_mock_data_generator.py -v
```

## Requirements Validation

This implementation satisfies:
- **Requirement 8.1**: Mock signals for 8 engineers, 3 projects
- **Requirement 8.2**: Realistic values for all five risk dimensions
- **Requirement 8.3**: At least one risk per severity level
