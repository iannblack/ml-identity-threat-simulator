"""
IAM Playbooks module.
Generates gcloud commands for IAM policy remediation.
"""


def revoke_binding_cmd(project_id: str, role: str, member: str) -> str:
    """
    Generate gcloud command to revoke an IAM binding.
    
    Args:
        project_id: GCP project ID
        role: IAM role to revoke
        member: Member to revoke the role from
        
    Returns:
        gcloud command string
    """
    return f"gcloud projects remove-iam-policy-binding {project_id} --member='{member}' --role='{role}'"


def add_binding_cmd(project_id: str, role: str, member: str) -> str:
    """
    Generate gcloud command to add an IAM binding.
    
    Args:
        project_id: GCP project ID
        role: IAM role to add
        member: Member to grant the role to
        
    Returns:
        gcloud command string
    """
    return (
        f"gcloud projects add-iam-policy-binding {project_id} --member='{member}' --role='{role}'"
    )
