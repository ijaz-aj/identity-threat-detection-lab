# References

Every fact this project relies on (schemas, APIs, licence requirements, free-tier rules, tool
behaviour) is listed here with its official source and the date it was checked.
Anything that could not be verified is marked **UNVERIFIED**.

## Platform and tooling
| Fact | Source | Checked |
|---|---|---|
| Splunk SOAR (On-premises) 6.4.1 evaluation needs "1 CPU with a minimum of 4 cores", "Minimum 8GB RAM, recommended 16GB", "Minimum 500GB of disk space" | [Splunk Docs: System requirements for evaluation use (6.4.1)](https://help.splunk.com/en/splunk-soar/soar-on-premises/install-and-upgrade-soar-on-premises/6.4.1/system-requirements/system-requirements-for-evaluation-use) | 2026-10-31 |
| Splunk SOAR supported OS: RHEL 8/9, Amazon Linux 2023, Oracle Linux 8/9 | [Splunk Docs: General system requirements (6.4.0)](https://help.splunk.com/en/splunk-soar/soar-on-premises/install-and-upgrade-soar-on-premises/6.4.0/system-requirements/general-system-requirements) | 2026-10-31 |
| Kusto emulator: image `mcr.microsoft.com/azuredataexplorer/kustainer-linux`, `ACCEPT_EULA=Y` required, engine on port 8080, needs SSE4.2/AVX2 and ≥2 GB RAM (4 GB recommended), **no HTTPS and no Microsoft Entra authentication**, image is several GB | [Microsoft Learn: Install the Kusto emulator](https://learn.microsoft.com/en-us/azure/data-explorer/kusto-emulator-install) | 2026-10-31 |
| Ollama binds 127.0.0.1:11434 by default; `OLLAMA_HOST` overrides it | [Ollama FAQ](https://docs.ollama.com/faq) | 2026-10-31 |
| Dependabot `package-ecosystem` values `github-actions`, `pip`, `pre-commit`; `cooldown` / `default-days` option | [GitHub Docs: Dependabot options reference](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference) | 2026-10-31 |
| gitleaks pre-commit hook `gitleaks` runs `gitleaks git --pre-commit --redact --staged --verbose` (staged changes only) | [gitleaks v8.30.1 `.pre-commit-hooks.yaml`](https://github.com/gitleaks/gitleaks/blob/v8.30.1/.pre-commit-hooks.yaml) | 2026-10-31 |
| ruff-pre-commit v0.17.1 hook ids `ruff-check`, `ruff-format` | [ruff-pre-commit `.pre-commit-hooks.yaml`](https://github.com/astral-sh/ruff-pre-commit/blob/v0.17.1/.pre-commit-hooks.yaml) | 2026-10-31 |
| `.gitignore`: `#` starts a comment only at the beginning of a line; `!` negates; last matching pattern wins | [git-scm: gitignore](https://git-scm.com/docs/gitignore) | 2026-10-31 (also proven locally with `git check-ignore`) |

## Log schemas and event names (Phase 1)
| Fact | Source | Checked |
|---|---|---|
| `SigninLogs` columns used here: `TimeGenerated`, `UserPrincipalName`, `IPAddress`, `Location`, `LocationDetails` (dynamic), `AutonomousSystemNumber`, `ResultType` ("0 indicates success; other values are failures"), `ResultDescription`, `AppDisplayName`, `ClientAppUsed`, `UserAgent`, `DeviceDetail` (dynamic), `IsInteractive` (bool), `AuthenticationDetails`, `AuthenticationRequirement`, `ConditionalAccessStatus`, `RiskLevelDuringSignIn` (P2 only, else `hidden`), `SessionId`, `UniqueTokenIdentifier`, `CorrelationId`. `MfaDetail` is **deprecated**. Ingestion API support: **No** (synthetic data needs a custom table). | [Azure Monitor table reference: SigninLogs](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/signinlogs) | 2026-11-01 |
| `AuditLogs` columns: `TimeGenerated`, `OperationName`, `ActivityDisplayName`, `Category`, `Result`, `ResultReason`, `InitiatedBy` (dynamic), `TargetResources` (dynamic), `AdditionalDetails` (dynamic), `LoggedByService`, `CorrelationId`, `Identity`. Ingestion API support: **No**. | [Azure Monitor table reference: AuditLogs](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/auditlogs) | 2026-11-01 |
| Sign-in error codes: 50126 InvalidUserNameOrPassword; 50053 account locked (IdsLocked) or sign-in from malicious IP blocked; 50057 UserDisabled; 50055 password expired; 50074 user did not pass the MFA challenge; 50076 MFA required; 53003 BlockedByConditionalAccess; 50140 KmsiInterrupt (normal "Keep me signed in" step) | [Microsoft Entra error codes](https://learn.microsoft.com/en-us/entra/identity-platform/reference-error-codes) | 2026-11-01 |
| 500121 "Authentication failed during strong authentication request." (not on the Learn page; from Microsoft's error lookup) | [login.microsoftonline.com/error?code=500121](https://login.microsoftonline.com/error?code=500121) | 2026-11-01 |
| Audit activities (category): `Consent to application`, `Add delegated permission grant`, `Add app role assignment to service principal`, `Add service principal credentials`, `Update application - Certificates and secrets management` (ApplicationManagement); `Add member to role`, `Add eligible member to role` (RoleManagement); `Add user`, `Reset password`, `Disable account` (UserManagement) | [Microsoft Entra audit log activity reference](https://learn.microsoft.com/en-us/entra/identity/monitoring-health/reference-audit-activities) | 2026-11-01 |

## Incident response facts
| Fact | Source | Checked |
|---|---|---|
| AWS applies the managed policy `AWSCompromisedKeyQuarantineV3` (earlier V2/V1) to an IAM user whose credentials are exposed publicly; it denies risky actions to limit fraud while leaving existing resources running | [AWS Managed Policy reference: AWSCompromisedKeyQuarantineV3](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSCompromisedKeyQuarantineV3.html) | 2026-11-01 |
| Exposed-key remediation order: deactivate the key, revoke active sessions, review CloudTrail, delete resources you didn't create, create a new key, delete the old key; keep the quarantine policy until all steps are done | [AWS re:Post Knowledge Center: Resolve unauthorized activity](https://repost.aws/knowledge-center/potential-account-compromise), [AWS re:Post: Responding to an exposed AWS access key](https://repost.aws/articles/ARTdf-AQfbTy--wzQmf2JOOg/managing-exposed-aws-access-keys-part-3-recovery-responding-to-an-exposed-aws-access-key) | 2026-11-01 |

## Known issues hit in this lab
| Issue | Source | Checked |
|---|---|---|
| Docker Desktop on Windows crashes on start when stale AF_UNIX socket files (`dockerInference`, `docker-secrets-engine\engine.sock`) can't be removed (error 1920); renaming the parent folder works | [docker/desktop-feedback #460](https://github.com/docker/desktop-feedback/issues/460), [#531](https://github.com/docker/desktop-feedback/issues/531), [#554](https://github.com/docker/desktop-feedback/issues/554), [#786](https://github.com/docker/desktop-feedback/issues/786) | 2026-10-31 |

## Pinned versions (Phase 0)
| Component | Version | Pinned as | Published |
|---|---|---|---|
| actions/checkout | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` | 2026-07-20 |
| actions/setup-python | v7.0.0 | `5fda3b95a4ea91299a34e894583c3862153e4b97` | 2026-07-20 |
| pre-commit/pre-commit-hooks | v6.0.0 | `3e8a8703264a2f4a69428a0aa4dcb512790b2c8c` | 2025-08-09 |
| astral-sh/ruff-pre-commit | v0.17.1 | `38bfb07c0c64c304f47eb52090f8288150c77730` | 2026-10-15 |
| adrienverge/yamllint | v1.38.0 | `cba56bcde1fdd01c1deb3f945e69764c291a6530` | 2026-01-13 |
| gitleaks | v8.30.1 | hook `83d9cd684c87d95d656c1458ef04895a7f1cbd8e`; image `sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f` | 2026-03-21 |
| pre-commit (pip) | 4.7.0 | `requirements-dev.txt` | 2026-10-13 |
