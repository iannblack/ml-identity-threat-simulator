"""
Gemini integration for AI-powered security advice.
"""

import logging
import os

from src.core.models import Finding

logger = logging.getLogger("iam-simulator")


class GeminiAdvisor:
    """Wrapper for Google Gemini API to explain security findings."""

    def __init__(self, api_key: str | None = None):
        """Initialize the Gemini Advisor."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            msg = "GOOGLE_API_KEY not found. Set it in your environment to use GenAI features."
            raise ValueError(msg)

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-pro")
        except ImportError as err:
            msg = (
                "The 'google-generativeai' library is required. "
                "Install it using: pip install google-generativeai"
            )
            raise ImportError(msg) from err

    def explain_finding(self, finding: Finding) -> str:
        """
        Generate a detailed explanation and remediation advice for a finding.
        """
        compliance_str = ", ".join(finding.compliance) if finding.compliance else "None"

        prompt = f"""
        You are an expert Cloud Security Engineer. Explain the following IAM security finding
        in simple terms to a developer or DevOps engineer.

        **Finding Context:**
        - **ID:** {finding.id}
        - **Severity:** {finding.severity}
        - **Description:** {finding.description}
        - **Resource:** {finding.resource}
        - **Details:** {finding.details}
        - **Compliance Violations:** {compliance_str}

        **Task:**
        Provide a concise but comprehensive analysis covering:
        1. **Risk Analysis:** What is the actual danger? What attacks does this enable?
        2. **Remediation:** How to fix it specifically (JSON examples or CLI commands if applicable).
        3. **Compliance Context:** Why does valid compliance frameworks (CIS, NIST) flag this?

        Format output in clear Markdown.
        """

        try:
            response = self.model.generate_content(prompt)
            return str(response.text)
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"Error generating explanation: {e}"
