"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path
from hypothesis import settings, Verbosity

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure hypothesis for property-based testing
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=200, verbosity=Verbosity.verbose)
settings.load_profile("default")


@pytest.fixture
def sample_team_id():
    """Sample team identifier."""
    return "team-alpha"


@pytest.fixture
def sample_signal_metadata():
    """Sample signal metadata."""
    from models import SignalMetadata
    return SignalMetadata(
        team_size=8,
        project_count=3,
        aggregation_period="weekly"
    )
