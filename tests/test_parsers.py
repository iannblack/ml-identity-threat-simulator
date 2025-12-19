from src.iam.parsers import extract_bindings_from_policy

def test_extract_bindings():
    policy = {"bindings":[{"role":"roles/owner","members":["user:a"]},{"role":"roles/viewer","members":["allAuthenticatedUsers"]}]}
    res = extract_bindings_from_policy(policy)
    assert {"role":"roles/owner","member":"user:a"} in res
    assert {"role":"roles/viewer","member":"allAuthenticatedUsers"} in res
