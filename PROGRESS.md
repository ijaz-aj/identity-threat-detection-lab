# Progress

## Phase 0 — Environment, repo, skeleton (in progress)

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
- [ ] Branch protection on `main` with required checks `lint` + `secret-scan`.
- [ ] First `LEARNING_LOG.md` entry.
