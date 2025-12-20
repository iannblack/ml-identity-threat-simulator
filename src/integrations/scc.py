from __future__ import annotations

import logging
from datetime import datetime, timezone

try:
    from google.cloud import securitycenter
    from google.protobuf import timestamp_pb2
except ImportError:
    securitycenter = None  # type: ignore
    timestamp_pb2 = None

from src.core.models import Finding

logger = logging.getLogger("iam-simulator")


class SCCExporter:
    """Exports Findings to Google Cloud Security Command Center."""

    def __init__(self, org_id: str, source_id: str) -> None:
        if securitycenter is None:
            msg = "google-cloud-securitycenter is not installed"
            raise ImportError(msg)

        self.org_id = org_id
        self.source_id = source_id
        # Client initialization might fail if credentials are not set
        try:
            self.client = securitycenter.SecurityCenterClient()
        except Exception as e:
            logger.error(f"Failed to initialize SCC client: {e}")
            raise

        self.parent = f"organizations/{org_id}/sources/{source_id}"

    def export(self, findings: list[Finding]) -> int:
        """
        Exports a list of findings to SCC.
        Returns the number of findings successfully exported.
        """
        success_count = 0
        now = datetime.now(timezone.utc)
        event_time = timestamp_pb2.Timestamp()
        event_time.FromDatetime(now)

        for finding in findings:
            finding_id = f"iam-sim-{finding.id.lower()}-{int(now.timestamp())}"
            # SCC finding name must be unique per source
            # Format: organizations/{org_id}/sources/{source_id}/findings/{finding_id}
            # finding_id limit is 32 chars usually, but we need to be careful.
            # actually SCC finding ID simply needs to be unique within the source.
            # Let's use a hash or just ID + short timestamp.

            # Map severity
            severity_map = {
                "CRITICAL": securitycenter.Finding.Severity.CRITICAL,
                "HIGH": securitycenter.Finding.Severity.HIGH,
                "MEDIUM": securitycenter.Finding.Severity.MEDIUM,
                "LOW": securitycenter.Finding.Severity.LOW,
            }
            scc_severity = severity_map.get(
                finding.severity, securitycenter.Finding.Severity.SEVERITY_UNSPECIFIED
            )

            scc_finding = securitycenter.Finding(
                state=securitycenter.Finding.State.ACTIVE,
                category=finding.id,
                severity=scc_severity,
                event_time=event_time,
                description=finding.description,
                source_properties=finding.details or {},
            )

            # Add resource name to source properties if possible, or use resource_name field
            # finding.resource often isn't a full resource name, so be careful.
            # We'll put it in properties for now.
            if finding.resource:
                scc_finding.source_properties["audit_resource"] = finding.resource

            try:
                self.client.create_finding(
                    request={
                        "parent": self.parent,
                        "finding_id": finding_id,
                        "finding": scc_finding,
                    }
                )
                success_count += 1
                logger.debug(f"Exported finding {finding_id} to SCC")
            except Exception as e:
                logger.error(f"Failed to export finding {finding.id} to SCC: {e}")

        logger.info(f"Successfully exported {success_count}/{len(findings)} findings to SCC")
        return success_count
