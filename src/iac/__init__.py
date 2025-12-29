"""
Infrastructure as Code (IaC) integration module.
Supports parsing and scanning of Terraform plans for IAM security risks.
"""

from .scanner import IacScanner
from .terraform import TerraformParser

__all__ = ["IacScanner", "TerraformParser"]
