from src.iam.parsers import extract_bindings_from_policy

def test_extract_bindings():
    policy={"bindings":[{"role":"roles/owner","members":["user:a"]}]}
    assert extract_bindings_from_policy(policy)==[{"role":"roles/owner","member":"user:a"}]
