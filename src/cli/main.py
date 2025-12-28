import json
import os
import sys

import click
from rich.console import Console
from rich.table import Table

from src.core.config import AppConfig
from src.core.logger import setup_logger
from src.core.models import AwsPolicy, AzureRoleDefinition, Finding, Policy
from src.iam.auditor import IAMAuditor
from src.iam.aws_auditor import AwsAuditor
from src.iam.aws_parsers import load_aws_policy_from_json
from src.iam.azure_auditor import AzureAuditor
from src.iam.azure_parsers import load_azure_role_from_json
from src.iam.parsers import load_policy_from_json
from src.simulator.runner import ScenarioRunner

console = Console()
logger = setup_logger()


@click.group()
def cli() -> None:
    """ML Identity Threat Simulator CLI"""


@cli.command()
@click.option("--policy", required=True, help="Path to IAM policy JSON file")
@click.option("--config", default="config.yaml", help="Path to configuration file")
@click.option("--out", default="findings.json", help="Output file for findings")
@click.option(
    "--provider",
    default="gcp",
    type=click.Choice(["gcp", "aws", "azure"]),
    help="Cloud provider (gcp, aws, azure)",
)
@click.option("--export-to-scc", is_flag=True, help="Export findings to Google SCC")
@click.option("--scc-org", help="Google Cloud Organization ID (required for SCC export)")
@click.option("--scc-source", help="SCC Source ID (required for SCC export)")
def audit(
    policy: str,
    config: str,
    out: str,
    provider: str,
    export_to_scc: bool,
    scc_org: str | None,
    scc_source: str | None,
) -> None:
    """Audit an IAM policy for risks."""
    logger.info(f"Starting {provider.upper()} audit on {policy} using config {config}")

    try:
        app_config = AppConfig.load(config)

        findings: list[Finding] = []
        if provider == "gcp":
            auditor = IAMAuditor(app_config)
            policy_obj = load_policy_from_json(policy)
            findings = auditor.audit_policy(policy_obj)
        elif provider == "aws":
            aws_auditor = AwsAuditor(app_config)
            aws_policy = load_aws_policy_from_json(policy)
            findings = aws_auditor.audit_policy(aws_policy)
        elif provider == "azure":
            azure_auditor = AzureAuditor(app_config)
            role_def = load_azure_role_from_json(policy)
            findings = azure_auditor.audit_policy(role_def)

        # Display results
        table = Table(title=f"Audit Findings ({len(findings)})")
        table.add_column("Severity", style="magenta")
        table.add_column("ID", style="cyan")
        table.add_column("Description", style="white")

        for f in findings:
            table.add_row(f.severity, f.id, f.description)

        console.print(table)

        # Export to File
        with open(out, "w") as file_out:
            json.dump([f.model_dump() for f in findings], file_out, indent=2)

        logger.info(f"Findings exported to {out}")

        # Export to SCC
        if export_to_scc:
            if not scc_org or not scc_source:
                console.print(
                    "[bold red]Error:[/bold red] --scc-org and --scc-source are required for SCC export."
                )
            else:
                try:
                    from src.integrations.scc import SCCExporter

                    console.print("[yellow]Exporting to Security Command Center...[/yellow]")
                    exporter = SCCExporter(scc_org, scc_source)
                    count = exporter.export(findings)
                    console.print(f"[green]Successfully exported {count} findings to SCC.[/green]")
                except ImportError:
                    console.print(
                        "[bold red]Error:[/bold red] google-cloud-securitycenter not installed."
                    )
                except Exception as e:
                    console.print(f"[bold red]SCC Export Failed:[/bold red] {e}")

    except Exception:
        logger.exception("An error occurred during execution")
        raise click.Abort from None


@cli.command()
@click.option("--scenario", required=True, help="Path to scenario YAML file")
@click.option("--out", default="simulation_result.json", help="Output file")
def simulate(scenario: str, out: str) -> None:
    """Run a threat scenario simulation."""
    logger.info(f"Running scenario: {scenario}")

    try:
        runner = ScenarioRunner()
        result = runner.run(scenario)

        console.print(f"[bold green]Scenario:[/bold green] {result.scenario_name}")

        for check in result.checks:
            console.print(f" - {check.description} [{check.status}]")

        # Export
        with open(out, "w") as f:
            f.write(result.model_dump_json(indent=2))

        logger.info(f"Results exported to {out}")

    except Exception:
        logger.exception("Simulation failed")
        raise click.Abort from None


@cli.command()
def dashboard() -> None:
    """Launch the interactive web dashboard."""
    from streamlit.web import cli as stcli

    logger.info("Launching dashboard...")

    # Resolve path to dashboard app
    # src/cli/main.py -> ../dashboard/app.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_path = os.path.join(current_dir, "..", "dashboard", "app.py")

    if not os.path.exists(dashboard_path):
        console.print(f"[bold red]Error:[/bold red] Dashboard app not found at {dashboard_path}")
        return

    # Invoke streamlit
    sys.argv = ["streamlit", "run", dashboard_path]
    sys.exit(stcli.main())


@cli.command()
@click.option(
    "--policies",
    required=True,
    multiple=True,
    help="Paths to policy JSON files for training (can specify multiple)",
)
@click.option(
    "--provider",
    default="gcp",
    type=click.Choice(["gcp", "aws", "azure"]),
    help="Cloud provider type",
)
@click.option("--model-path", default="models/anomaly_detector.pkl", help="Path to save model")
@click.option(
    "--contamination", default=0.1, type=float, help="Expected proportion of anomalies (0.0-0.5)"
)
def ml_train(
    policies: tuple[str, ...], provider: str, model_path: str, contamination: float
) -> None:
    """Train ML model for anomaly detection on IAM policies."""
    logger.info(f"Training ML model on {len(policies)} {provider.upper()} policies")

    try:
        from src.ml.detector import AnomalyDetector
        from src.ml.models import MLConfig

        # Load all policies
        policy_objects: list[Policy | AwsPolicy | AzureRoleDefinition] = []
        for policy_path in policies:
            if provider == "gcp":
                policy_obj = load_policy_from_json(policy_path)
            elif provider == "aws":
                policy_obj = load_aws_policy_from_json(policy_path)
            elif provider == "azure":
                policy_obj = load_azure_role_from_json(policy_path)
            else:
                console.print(f"[bold red]Error:[/bold red] Unknown provider: {provider}")
                return

            policy_objects.append(policy_obj)

        # Configure and train detector
        ml_config = MLConfig(contamination=contamination, model_path=model_path)
        detector = AnomalyDetector(config=ml_config)

        with console.status("[bold yellow]Training model..."):
            detector.train(policy_objects, save_model=True)

        console.print("[bold green]✓ Model trained successfully[/bold green]")
        console.print(f"  Model saved to: {model_path}")
        console.print(f"  Training samples: {len(policy_objects)}")
        console.print(f"  Contamination rate: {contamination}")

    except Exception as e:
        logger.exception("ML training failed")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort from None


@cli.command()
@click.option("--policy", required=True, help="Path to IAM policy JSON file to analyze")
@click.option(
    "--provider",
    default="gcp",
    type=click.Choice(["gcp", "aws", "azure"]),
    help="Cloud provider type",
)
@click.option("--model-path", default="models/anomaly_detector.pkl", help="Path to trained model")
@click.option("--out", default="anomaly_result.json", help="Output file for results")
def ml_detect(policy: str, provider: str, model_path: str, out: str) -> None:
    """Detect anomalies in an IAM policy using trained ML model."""
    logger.info(f"Analyzing policy {policy} for anomalies")

    try:
        from src.ml.detector import AnomalyDetector

        # Load policy
        policy_obj: Policy | AwsPolicy | AzureRoleDefinition
        if provider == "gcp":
            policy_obj = load_policy_from_json(policy)
        elif provider == "aws":
            policy_obj = load_aws_policy_from_json(policy)
        elif provider == "azure":
            policy_obj = load_azure_role_from_json(policy)
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown provider: {provider}")
            return

        # Load detector and predict
        detector = AnomalyDetector()
        detector.load_model(model_path)

        with console.status("[bold yellow]Analyzing policy..."):
            result = detector.predict(policy_obj)

        # Display results
        if result.is_anomaly:
            console.print("\n[bold red]⚠ ANOMALY DETECTED[/bold red]")
            console.print(f"  Confidence: {result.confidence:.1%}")
            console.print(f"  Anomaly Score: {result.anomaly_score:.3f}")
        else:
            console.print("\n[bold green]✓ Policy appears normal[/bold green]")
            console.print(f"  Confidence: {result.confidence:.1%}")
            console.print(f"  Anomaly Score: {result.anomaly_score:.3f}")

        console.print("\n[bold]Explanation:[/bold]")
        console.print(f"  {result.explanation}")

        if result.risk_factors:
            console.print("\n[bold yellow]Risk Factors:[/bold yellow]")
            for factor in result.risk_factors:
                console.print(f"  • {factor}")

        # Export results
        with open(out, "w") as f:
            json.dump(result.model_dump(), f, indent=2)

        console.print(f"\n[dim]Results saved to {out}[/dim]")

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("\n[yellow]Tip:[/yellow] Train a model first using: iam-simulator ml-train")
        raise click.Abort from None
    except Exception as e:
        logger.exception("ML detection failed")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort from None


if __name__ == "__main__":
    cli()
