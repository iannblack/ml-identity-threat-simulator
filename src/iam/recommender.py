"""
IAM Recommender integration module.
Provides suggestions for IAM policy improvements.
"""

from typing import Any, Dict, List


def suggest_removals(findings: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Suggest IAM binding removals or replacements based on findings.
    
    Args:
        findings: List of finding dictionaries with binding information
        
    Returns:
        List of suggestion dictionaries with action, member, from, and to fields
    """
    suggestions: List[Dict[str, str]] = []
    for f in findings:
        role: str = f["binding"]["role"]
        member: str = f["binding"]["member"]
        if role in {"roles/owner", "roles/editor"}:
            suggestions.append(
                {"action": "replace", "member": member, "from": role, "to": "roles/viewer"}
            )
    return suggestions
