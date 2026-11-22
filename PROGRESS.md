# Progress

## Phase 1 — Telemetry and labelled attack data (in progress)

### Session 2 — 2026-11-01
- Verified on Microsoft Learn and recorded in `docs/references.md`: `SigninLogs` and `AuditLogs`
  columns (`MfaDetail` is deprecated; neither table supports the Logs Ingestion API, so synthetic
  data will need a custom table), sign-in error codes (0, 50126, 50053, 50057, 50074, 50076,
  500121, 53003, 50140) and audit activity names for role, consent and app-credential changes.
- Learned the identity attack chain: password spray → MFA fatigue → AiTM token theft → inbox rule →
  OAuth consent → privilege escalation, and which table shows each step.
- TRY (triage 9 synthetic sign-ins): identified the spray (6 users, 1 IP, 33 s, 50126), the
  successful sign-in from the spray IP as the priority, the benign typo-then-success, and a
  contain → investigate → remediate response.

### Session 3 — 2026-11-07 and 2026-11-22
- Verified and recorded Microsoft 365 sources: `OfficeActivity` columns, `CloudAppEvents` (needs
  Defender for Cloud Apps), Exchange audit operations (`New-InboxRule`, `Set-InboxRule`,
  `UpdateInboxRules`, `MailItemsAccessed`, …) and `New-InboxRule` parameters.
- TRY (triage 5 synthetic mailbox events): identified mail access + hiding rule + external forward
  from the spray IP (pivot on `ClientIP`), a benign newsletter rule, and the business impact of
  `MailItemsAccessed`. Still to practise: deciding on events with missing detail.
- Plan change: added a verify-first, zero-cost **Microsoft ISOC** track (Phases 2, 5, 6). Trial
  eligibility and workspace billing are UNVERIFIED and listed in `docs/references.md`.
- First Dependabot review: #3 (setup-python 7.1.0) and #8 + #9 (ruff 0.17.4, merged as a pair) approved
  after verifying each pinned SHA against the official tag, reading release notes (no breaking
  changes; ruff's new security rule is preview-only), and checking the 14-day cooldown. Dependabot had
  superseded #4–#7 itself. Note: ruff's green CI exercised nothing yet (0 Python files).
  Two `main` CI runs showed "cancelled" by design (`cancel-in-progress`); the final run was green.

### Session 4 — 2026-11-22
- Verified `AWSCloudTrail`, `AzureActivity`, `SecurityEvent` schemas, CloudTrail/IAM/S3 event names,
  console sign-in fields and Windows event IDs (`docs/references.md`). Findings that matter later:
  S3 object-level data events are off by default and cost extra; `AWSCloudTrail` supports the
  Logs Ingestion API.
- **Kusto emulator running locally** (`docker-compose.yml`): pinned by digest to a ≥14-day-old
  weekly production build; port bound to `127.0.0.1` and proven unreachable from Wi-Fi, VirtualBox
  and WSL addresses; 4 GB / 2 CPU limits; `no-new-privileges`. Gap: runs as root.
- `scripts/kql.py` helper; `data/samples/password_spray_mini.kql` (9 rows from the first TRY).
- **KQL training week** (`data/training/`): 6 tables, 2,271 synthetic rows, 19 hidden scenarios in
  three tiers plus benign look-alikes; sanity-checked (the spray IP stands out with 16 users;
  14 benign typo failures exist as noise).
- Decision: pause the project build to take an 8-module KQL course on this data first.

**Next:** KQL Module 1 exercises → Module 2 (aggregation and time windows) on the training week.

## Phase 0 — Environment, repo, skeleton (complete)

### Session 1 — 2026-10-31
**Environment**
- Hardware: AMD Ryzen 7 7445HS (6 cores / 12 threads), 15.3 GB RAM, ~44 GB free disk on C:.
- Present: git 2.55, Python 3.14.5 + pip 26.1, gh 2.100, Docker Desktop (engine 29.6.1, WSL2),
  VirtualBox 7.2.6 (existing VM `DaC-Win10-Endpoint`), winget.
- Installed: Azure CLI 2.91.0, Bicep 0.48.1, AWS CLI 2.39.3.
- Fixed: Docker Desktop crash loop (known bug, stale socket files) → `scripts/fix_docker_stale_sockets.ps1`.

**Decisions**
- Second SOAR = **Shuffle** (Splunk SOAR needs 500 GB disk + 8–16 GB RAM VM). See `docs/architecture.md`.
- Repo name: `identity-threat-detection-lab`.
- Commits use my GitHub noreply email, so my personal address never appears in public history.

**Built**
- Repo skeleton (folders with purpose READMEs), `.gitignore` (tested with `git check-ignore`),
  `.env.example`, `README.md`, MIT `LICENSE`, `docs/architecture.md`, `docs/threat-model.md`,
  `docs/references.md`, `docs/tools.md`.
- Quality gates: pre-commit (file hygiene, ruff, yamllint, gitleaks); CI workflow (`lint` +
  full-history `secret-scan`); Dependabot.
- Verified locally: all pre-commit checks pass; the CI gitleaks command scans history with no leaks.

**Published**
- Public repo: https://github.com/ijaz-aj/identity-threat-detection-lab (description + 12 topics).
- First CI run green on `0dcf757`: `lint` and `secret-scan` passed; log shows "1 commits scanned …
  no leaks found". Run: https://github.com/ijaz-aj/identity-threat-detection-lab/actions/runs/41228769904

**Open**
- [x] Control validation: a fake GitHub token was blocked at commit time (`RuleID: github-pat`,
      entropy 5.27, secret shown as REDACTED); test file removed afterwards.
- [ ] Verify `.env` ignore rules with `git check-ignore -v .env .env.local .env.example`.
- [x] Ruleset `protect-main` (active, no bypass): PR required, required checks `lint (pre-commit)` and
      `secret scan (gitleaks, full history)`, force pushes and deletion blocked. Validated: a direct
      push to `main` was rejected (`GH013: Changes must be made through a pull request`); PR #1 merged
      after both checks passed.
- [x] First `LEARNING_LOG.md` entry.
