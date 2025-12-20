import json

import click
from rich.console import Console
from rich.table import Table

from src.core.config import AppConfig
from src.core.logger import setup_logger
from src.core.models import Finding
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
def audit(policy: str, config: str, out: str, provider: str) -> None:
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

        # Export
        with open(out, "w") as file_out:
            json.dump([f.model_dump() for f in findings], file_out, indent=2)

        logger.info(f"Findings exported to {out}")

    except Exception:
        logger.exception("Audit failed")
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


if __name__ == "__main__":
    cli()
