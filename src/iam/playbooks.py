def revoke_binding_cmd(project_id, role, member):
    return f"gcloud projects remove-iam-policy-binding {project_id} --member='{member}' --role='{role}'"
