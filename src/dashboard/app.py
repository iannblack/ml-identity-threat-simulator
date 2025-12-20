import os
import tempfile

import pandas as pd
import plotly.express as px
import streamlit as st

from src.core.config import AppConfig
from src.core.models import Finding
from src.iam.auditor import IAMAuditor
from src.iam.aws_auditor import AwsAuditor
from src.iam.aws_parsers import load_aws_policy_from_json
from src.iam.azure_auditor import AzureAuditor
from src.iam.azure_parsers import load_azure_role_from_json
from src.iam.parsers import load_policy_from_json

st.set_page_config(
    page_title="IAM Threat Simulator",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ IAM Threat Simulator Dashboard")
st.markdown(
    """
    Upload your IAM policies (GCP, AWS) or Role Definitions (Azure) to audit them for security risks.
    """
)

# Sidebar for configuration
st.sidebar.header("Configuration")
provider = st.sidebar.selectbox("Cloud Provider", ["GCP", "AWS", "Azure"])

uploaded_file = st.sidebar.file_uploader("Upload Policy/Role JSON", type=["json"])

# Load Config
# For the dashboard, we use default safe config or could allow uploading a config file
app_config = AppConfig(risky_roles=[], wildcard_members=[])


def run_audit(file_path: str, provider: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        if provider == "GCP":
            auditor = IAMAuditor(app_config)
            gcp_policy = load_policy_from_json(file_path)
            findings = auditor.audit_policy(gcp_policy)
        elif provider == "AWS":
            aws_auditor = AwsAuditor(app_config)
            aws_policy = load_aws_policy_from_json(file_path)
            findings = aws_auditor.audit_policy(aws_policy)
        elif provider == "Azure":
            azure_auditor = AzureAuditor(app_config)
            role = load_azure_role_from_json(file_path)
            findings = azure_auditor.audit_policy(role)
    except Exception as e:
        st.error(f"Error auditing file: {e}")
        return []

    return findings


if uploaded_file is not None:
    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        with st.spinner(f"Auditing {provider} policy..."):
            findings = run_audit(tmp_path, provider)

        # Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        total = len(findings)
        critical = len([f for f in findings if f.severity == "CRITICAL"])
        high = len([f for f in findings if f.severity == "HIGH"])
        medium = len([f for f in findings if f.severity == "MEDIUM"])

        col1.metric("Total Findings", total)
        col2.metric("Critical", critical, delta_color="inverse" if critical > 0 else "off")
        col3.metric("High", high, delta_color="inverse" if high > 0 else "off")
        col4.metric("Medium", medium, delta_color="inverse" if medium > 0 else "off")

        if findings:
            # Create DataFrame for analysis
            df = pd.DataFrame([f.model_dump() for f in findings])

            # Severity Chart
            st.subheader("Severity Distribution")
            fig = px.pie(
                df,
                names="severity",
                title="Findings by Severity",
                color="severity",
                color_discrete_map={
                    "CRITICAL": "red",
                    "HIGH": "orange",
                    "MEDIUM": "yellow",
                    "LOW": "blue",
                },
            )
            st.plotly_chart(fig)

            # Detailed Table
            st.subheader("Detailed Findings")
            st.dataframe(
                df[["id", "severity", "description", "resource"]],
                use_container_width=True,
                hide_index=True,
            )

            # Expandable details
            st.subheader("Finding Details")
            for f in findings:
                with st.expander(f"[{f.severity}] {f.id} - {f.description}"):
                    st.json(f.model_dump())
        else:
            st.success("No security risks found! 🎉")

    finally:
        os.unlink(tmp_path)
else:
    st.info("👈 Please upload a JSON file to start the audit.")

    # Example instructions
    with st.expander("How to export policies?"):
        st.markdown(
            """
        **GCP:**
        ```bash
        gcloud projects get-iam-policy PROJECT_ID --format=json > policy.json
        ```

        **AWS:**
        Export a policy from AWS Console or CLI to JSON.

        **Azure:**
        ```bash
        az role definition list --name "MyRole" --output json > role.json
        ```
        """
        )
