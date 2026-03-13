import json
import pytest
from unittest.mock import patch, mock_open

from pydantic import ValidationError

from app.config import get_compatibility_profile
from app.models.compatibility import CompatibilityProfile

def test_default_profile_loads_fallback():
    with patch("pathlib.Path.exists", return_value=False), \
         patch("app.config.get_settings") as mock_settings:
        mock_settings.return_value.compatibility_profile = "balanced"
        
        profile = get_compatibility_profile()
        assert profile.name == "balanced"
        assert profile.retry_aggressiveness == "low"

def test_profile_change_emits_audit_log():
    yaml_content = b"""
profiles:
  strict_safe:
    retry_aggressiveness: low
  balanced:
    retry_aggressiveness: medium
"""
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.open", mock_open(read_data=yaml_content)), \
         patch("app.config.get_settings") as mock_settings, \
         patch("app.audit.log_task_event") as mock_log:
         
        # Load first profile
        mock_settings.return_value.compatibility_profile = "strict_safe"
        p1 = get_compatibility_profile()
        assert p1.name == "strict_safe"
        # Should not emit log on first load
        mock_log.assert_not_called()

        # Change profile
        mock_settings.return_value.compatibility_profile = "balanced"
        p2 = get_compatibility_profile()
        assert p2.name == "balanced"
        
        # Should emit log
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[0] == "compatibility_profile_changed"
        assert kwargs["details"]["old_profile"] == "strict_safe"
        assert kwargs["details"]["new_profile"] == "balanced"

