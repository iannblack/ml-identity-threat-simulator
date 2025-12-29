"""Tests for integration modules."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from src.core.models import Finding


class TestGeminiAdvisor:
    def test_init_raises_error_without_api_key(self):
        # Ensure env var is unset
        with (
            patch.dict(os.environ, {}, clear=True),
            # Mock genai so ImportError isn't raised first
            patch.dict(sys.modules, {"google.generativeai": MagicMock()}),
        ):
            from src.integrations.gemini import GeminiAdvisor

            with pytest.raises(ValueError, match="GOOGLE_API_KEY not found"):
                GeminiAdvisor()

    def test_explain_finding(self):
        finding = Finding(
            id="TEST_FINDING",
            severity="HIGH",
            description="Test description",
            compliance=["CIS 1.1"],
        )

        # Setup mock for google.generativeai
        mock_genai = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "AI explanation"
        mock_genai.GenerativeModel.return_value = mock_model

        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "fake-key"}),
            patch.dict(sys.modules, {"google.generativeai": mock_genai}),
        ):
            from src.integrations.gemini import GeminiAdvisor

            advisor = GeminiAdvisor()
            explanation = advisor.explain_finding(finding)

            assert explanation == "AI explanation"
            mock_model.generate_content.assert_called_once()
            # Verify call args contained finding info
            args = mock_model.generate_content.call_args[0][0]
            assert "TEST_FINDING" in args
            assert "CIS 1.1" in args
