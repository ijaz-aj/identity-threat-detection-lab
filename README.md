# Identity & Cloud Threat Detection Lab

[![ci](https://github.com/ijaz-aj/identity-threat-detection-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/ijaz-aj/identity-threat-detection-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Status: Phase 0 (repo skeleton and CI).** Work in progress. Nothing below is claimed until a
> generated results file or the sprint log proves it.

A **home lab** for detecting identity and cloud attacks with **Microsoft Sentinel and KQL**:
a tested detection library for Microsoft Entra ID, Microsoft 365, AWS CloudTrail and Windows,
SOAR playbooks, an AI triage agent with an evaluation harness, and a 30-day live Sentinel SOC sprint
against my own lab tenant and AWS account.

Companion project: [`detection-as-code`](https://github.com/ijaz-aj/detection-as-code) (Sigma rules for
Windows endpoint telemetry). This repo covers what that one doesn't: identity, cloud, Sentinel, SOAR and AI.

## What this will prove
_Filled in as phases complete, each point linked to evidence._

## Architecture
_Coming in Phase 2. Design reasoning: [docs/architecture.md](docs/architecture.md)._

## Results
_Generated from `docs/results/` once detections and tests exist (Phase 3)._

## Reviewer quickstart
_Coming in Phase 3: clone → `docker compose up -d` → `pytest`._

## Repository layout
| Folder | Contents |
|---|---|
| `data/` | Schemas, attack scenarios, synthetic log generator, labelled datasets |
| `detections/` | Sentinel analytics rules (YAML) for Entra ID, M365, AWS, Windows |
| `tests/` | Detection tests run in the Kusto emulator |
| `hunting/` | Threat hunts and reports |
| `playbooks/` | SOAR playbooks: Python, Logic Apps, Shuffle |
| `dfir/` | Velociraptor artifacts and endpoint case study |
| `triage_agent/`, `evals/` | AI triage agent and its evaluation harness |
| `infra/` | Bicep (Azure) and AWS IaC for the live lab |
| `lab/` | Attack plans, runbook, sprint log, cost guardrails, teardown proof |
| `docs/` | Architecture, detection standard, threat model, references, generated results |

## Tech stack
Microsoft Sentinel (Defender portal), KQL, Log Analytics, Entra ID, Microsoft 365, Logic Apps,
Bicep · AWS CloudTrail, S3, SQS, IAM, Stratus Red Team · Windows, Sysmon, Atomic Red Team ·
Velociraptor · Shuffle SOAR · Python, pytest, Kusto emulator, Docker, GitHub Actions, pre-commit,
gitleaks, ruff · Ollama, JSON Schema guardrails. Each tool is explained in [docs/tools.md](docs/tools.md).

## Limitations
- Home lab, not production. Data is clearly labelled as synthetic, public dataset, or live lab
  telemetry from my own test tenant and AWS account.
- The live Sentinel sprint runs on free trials for 30 days; after teardown, the emulator tests keep
  every rule reproducible without the cloud.

## License
[MIT](LICENSE)
