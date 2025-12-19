# 🛡️ ML Identity Threat Simulator

[![CI](https://github.com/ImNotKilian/ml-identity-threat-simulator/workflows/CI/badge.svg)](https://github.com/ImNotKilian/ml-identity-threat-simulator/actions)
[![codecov](https://codecov.io/gh/ImNotKilian/ml-identity-threat-simulator/branch/main/graph/badge.svg)](https://codecov.io/gh/ImNotKilian/ml-identity-threat-simulator)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

**IAM Threat Simulator for ML pipelines on Google Cloud Platform.** Analyzes Cloud Asset Inventory (CAI) exports, detects risky IAM bindings, simulates attack scenarios, and generates actionable remediation playbooks.

---

## 🚀 Features

- **🔍 IAM Policy Auditing** - Detect overly permissive roles, wildcard access, and service account misconfigurations
- **📊 Risk Scoring** - Quantify security risks with customizable severity levels (LOW, MEDIUM, HIGH, CRITICAL)
- **🎮 Threat Simulation** - Run attack scenarios to validate security controls
- **🛠️ Remediation Playbooks** - Generate actionable `gcloud` commands to fix issues
- **💻 Rich CLI** - Beautiful terminal output with tables and progress indicators
- **🔧 Extensible** - Easy to add custom rules and scenarios
- **🧪 Well-Tested** - 80%+ code coverage with comprehensive test suite
- **🔒 Security-First** - Automated security scanning with Bandit and Safety

---

## 📋 Table of Contents

- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Development](#-development)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📦 Prerequisites

- **Python 3.10 or higher**
- **Google Cloud SDK** (for remediation commands)
- **Access to GCP Cloud Asset Inventory exports** (optional, for production use)

---

## 🔧 Installation

### From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/ImNotKilian/ml-identity-threat-simulator.git
cd ml-identity-threat-simulator

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Verify installation
iam-simulator --help
```

### From PyPI (When Published)

```bash
pip install ml-identity-threat-simulator
```

### Using Docker 🐳

```bash
# Pull the image
docker pull imnotkilian/iam-simulator:latest

# Run with Docker
docker run --rm \
  -v $(pwd)/data:/app/data:ro \
  -v $(pwd)/output:/app/output:rw \
  iam-simulator:latest \
  audit --policy /app/data/policy.json --out /app/output/findings.json
```

### Build Locally

```bash
# Build the image
docker build -t iam-simulator:latest .

# Run container scan
docker run --rm -v $(pwd)/src:/app/src iam-simulator:latest audit --help
```

---

## ⚡ Quick Start

### 1. Export GCP IAM Policy

```bash
# Export your project's IAM policy
gcloud projects get-iam-policy YOUR_PROJECT_ID --format=json > policy.json
```

### 2. Run Audit

```bash
# Audit the policy for security risks
iam-simulator audit --policy policy.json --config config.yaml --out findings.json
```

**Example Output:**
```
╭─────────────────────────────────────────────────────────────────╮
│                    Audit Findings (3)                           │
├──────────┬─────────────────┬──────────────────────────────────────┤
│ Severity │ ID              │ Description                          │
├──────────┼─────────────────┼──────────────────────────────────────┤
│ CRITICAL │ WILDCARD_ACCESS │ Public access detected via           │
│          │                 │ 'allUsers' on role 'roles/viewer'    │
├──────────┼─────────────────┼──────────────────────────────────────┤
│ HIGH     │ RISKY_ROLE      │ Role 'roles/owner' is considered     │
│          │                 │ too permissive                       │
├──────────┼─────────────────┼──────────────────────────────────────┤
│ MEDIUM   │ SA_HIGH_PRIV    │ Service Account has broad            │
│          │                 │ privileges 'roles/editor'            │
╰──────────┴─────────────────┴──────────────────────────────────────╯

Findings exported to findings.json
```

### 3. Generate Report

```bash
# Generate a markdown report
python reports/risk_report.py --findings findings.json --out report.md
```

---

## 📚 Usage Examples

### Example 1: Basic Audit

```bash
iam-simulator audit \
  --policy my-policy.json \
  --config config.yaml \
  --out findings.json
```

### Example 2: Audit with Custom Configuration

Create a custom `config.yaml`:

```yaml
risky_roles:
  - roles/owner
  - roles/editor
  - roles/bigquery.admin
  - roles/storage.admin
  - roles/iam.securityAdmin

wildcard_members:
  - allUsers
  - allAuthenticatedUsers
```

Then run:

```bash
iam-simulator audit --policy policy.json --config custom-config.yaml
```

### Example 3: Run Threat Scenario

```bash
iam-simulator simulate \
  --scenario scenarios/privilege-escalation.yaml \
  --out simulation-result.json
```

### Example 4: Programmatic Usage

```python
from src.core.config import AppConfig
from src.core.models import Policy, Binding
from src.iam.auditor import IAMAuditor
from src.iam.parsers import load_policy_from_json

# Load configuration
config = AppConfig.load("config.yaml")

# Create auditor
auditor = IAMAuditor(config)

# Load and audit policy
policy = load_policy_from_json("policy.json")
findings = auditor.audit_policy(policy)

# Process findings
for finding in findings:
    print(f"[{finding.severity}] {finding.description}")
    if finding.remediation:
        print(f"  → Remediation: {finding.remediation}")
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Interface                            │
│                    (src/cli/main.py)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐            ┌─────────────────┐
│  IAM Auditor    │            │  Threat         │
│  (src/iam/)     │            │  Simulator      │
│                 │            │  (src/simulator)│
│  - auditor.py   │            │                 │
│  - parsers.py   │            │  - runner.py    │
│  - playbooks.py │            │  - scenarios/   │
└────────┬────────┘            └────────┬────────┘
         │                              │
         └──────────┬───────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │   Core Models    │
         │   (src/core/)    │
         │                  │
         │  - models.py     │
         │  - config.py     │
         │  - logger.py     │
         └──────────────────┘
```

### Project Structure

```
ml-identity-threat-simulator/
├── src/
│   ├── core/              # Core models and configuration
│   │   ├── models.py      # Pydantic models (Policy, Finding, etc.)
│   │   ├── config.py      # Configuration management
│   │   └── logger.py      # Logging setup
│   ├── iam/               # IAM analysis logic
│   │   ├── auditor.py     # Main auditing engine
│   │   ├── parsers.py     # Policy parsing utilities
│   │   ├── playbooks.py   # Remediation command generation
│   │   └── recommender.py # Recommendations engine
│   ├── simulator/         # Threat simulation
│   │   ├── runner.py      # Scenario execution engine
│   │   └── scenarios/     # Threat scenario definitions
│   └── cli/               # Command-line interface
│       └── main.py        # Click-based CLI
├── tests/                 # Comprehensive test suite (80%+ coverage)
├── reports/               # Report generation
├── config.yaml            # Default configuration
└── pyproject.toml         # Project configuration
```

---

## ⚙️ Configuration

### Configuration File (`config.yaml`)

```yaml
risky_roles:
  - roles/owner
  - roles/editor
  - roles/bigquery.admin
  - roles/storage.admin
  - roles/iam.securityAdmin

wildcard_members:
  - allUsers
  - allAuthenticatedUsers

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_ORGANIZATION_ID=your-org-id

# Logging
IAM_SIMULATOR_LOGGING_LEVEL=INFO
```

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone and navigate to project
git clone https://github.com/ImNotKilian/ml-identity-threat-simulator.git
cd ml-identity-threat-simulator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Quality Tools

```bash
# Format code with Black
black src/ tests/ reports/

# Lint with Ruff
ruff check src/ tests/ reports/

# Type check with mypy
mypy src/ --ignore-missing-imports

# Security scan with Bandit
bandit -r src/

# Check dependencies with Safety
safety check
```

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

- ✅ Trailing whitespace removal
- ✅ End-of-file fixer
- ✅ YAML/JSON validation
- ✅ Black formatting
- ✅ Ruff linting
- ✅ mypy type checking
- ✅ Bandit security scanning

Run manually on all files:

```bash
pre-commit run --all-files
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest -v
```

### Run Tests with Coverage

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

### View Coverage Report

```bash
# Open HTML report in browser
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Specific Test Files

```bash
# Test models
pytest tests/test_models.py -v

# Test configuration
pytest tests/test_config.py -v

# Test auditor
pytest tests/test_auditor.py -v

# Test parsers
pytest tests/test_parsers_new.py -v
```

### Test Coverage Goals

- ✅ **Overall Coverage:** ≥80%
- ✅ **Core Models:** ~95%
- ✅ **Configuration:** ~90%
- ✅ **IAM Auditor:** ~95%
- ✅ **Parsers:** ~90%

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

### 1. Fork the Repository

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/ml-identity-threat-simulator.git
cd ml-identity-threat-simulator
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/amazing-feature
```

### 3. Make Your Changes

- Write code following the project's style guide
- Add tests for new functionality
- Update documentation as needed

### 4. Run Quality Checks

```bash
# Format and lint
black src/ tests/
ruff check --fix src/ tests/

# Run tests
pytest --cov=src

# Type check
mypy src/
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: Add amazing feature

- Detailed description of changes
- Why this change is needed
- Any breaking changes"
```

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/amazing-feature
```

Then open a Pull Request on GitHub.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 ImNotKilian

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🙏 Acknowledgments

- Inspired by [GCP Security Best Practices](https://cloud.google.com/security/best-practices)
- Built with [Pydantic](https://pydantic-docs.helpmanual.io/), [Click](https://click.palletsprojects.com/), and [Rich](https://rich.readthedocs.io/)
- Security scanning powered by [Bandit](https://bandit.readthedocs.io/) and [Safety](https://pyup.io/safety/)

---

## 📞 Support

- **Documentation:** [GitHub Wiki](https://github.com/ImNotKilian/ml-identity-threat-simulator/wiki)
- **Issues:** [GitHub Issues](https://github.com/ImNotKilian/ml-identity-threat-simulator/issues)
- **Discussions:** [GitHub Discussions](https://github.com/ImNotKilian/ml-identity-threat-simulator/discussions)

---

## 🗺️ Roadmap

- [ ] Support for AWS IAM policies
- [ ] Support for Azure RBAC
- [ ] Interactive web dashboard
- [ ] Integration with Security Command Center
- [ ] ML-based anomaly detection
- [ ] Automated remediation workflows
- [ ] Terraform/Pulumi integration

---

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/ImNotKilian/ml-identity-threat-simulator?style=social)
![GitHub forks](https://img.shields.io/github/forks/ImNotKilian/ml-identity-threat-simulator?style=social)
![GitHub issues](https://img.shields.io/github/issues/ImNotKilian/ml-identity-threat-simulator)
![GitHub pull requests](https://img.shields.io/github/issues-pr/ImNotKilian/ml-identity-threat-simulator)
![GitHub last commit](https://img.shields.io/github/last-commit/ImNotKilian/ml-identity-threat-simulator)

---

<div align="center">

**Made with ❤️ for Cloud Security**

[⬆ Back to Top](#️-ml-identity-threat-simulator)

</div>
