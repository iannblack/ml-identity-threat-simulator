from src.iam.audit import score_binding

def test_score_binding():
    s,_=score_binding({"role":"roles/owner","member":"user:a"})
    assert s>=5
