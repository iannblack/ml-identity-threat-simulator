# Placeholder for integrating IAM Recommender exports.
def suggest_removals(findings):
    suggestions = []
    for f in findings:
        role = f["binding"]["role"]
        member = f["binding"]["member"]
        if role in {"roles/owner","roles/editor"}:
            suggestions.append({"action": "replace", "member": member, "from": role, "to": "roles/viewer"})
    return suggestions
