from src.iam.audit import score_binding

def test_score_binding_owner_user():
    b = {"role":"roles/owner","member":"user:admin@example.com"}
    score, reason = score_binding(b)
    assert score >= 5 and "risky-role:roles/owner" in reason

def test_score_binding_wildcard():
    b = {"role":"roles/viewer","member":"allAuthenticatedUsers"}
    score, reason = score_binding(b)
    assert score >= 5 and "wildcard-member" in reason
