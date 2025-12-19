def revoke_binding_cmd(project_id: str, role: str, member: str) -> str:
    return f"gcloud projects remove-iam-policy-binding {project_id} --member='{member}' --role='{role}'"

def add_binding_cmd(project_id: str, role: str, member: str) -> str:
    return f"gcloud projects add-iam-policy-binding {project_id} --member='{member}' --role='{role}'"
