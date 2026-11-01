# Threat model

Living document. Updated at the start of every phase that adds a new trust boundary.
Method: name the **assets**, the **actors**, the **entry points** and the **abuse cases**, then the
**controls** and the **gaps**. A control is listed as "in place" only when a test or command output proves it.

Last updated: Phase 0 (2026-10-31).

## Assets
| Asset | Why it matters |
|---|---|
| Cloud credentials (Azure, AWS, API keys in `.env`) | Full control of the lab tenant/account; could run up cost on my card |
| Lab identity data (tenant ID, subscription ID, personal email, home IP, phone) | Privacy; targeted phishing |
| Public GitHub repo and its history | Portfolio reputation; anything committed is public forever |
| CI pipeline (GitHub Actions) and, from Phase 5, its deploy identity | Could deploy changed rules or infrastructure into the live workspace |
| Detection rules | A silently broken rule is a false negative nobody notices |
| Evidence (screenshots, exports, Velociraptor collections) | Contains identifiers of the lab tenant and endpoints |

## Actors
- **Me, the repo owner** (trusted, but can make mistakes, e.g. commit a secret).
- **Anyone on the internet** reading the public repo, forking it, or opening pull requests.
- **Compromised upstream dependency** (a GitHub Action, pre-commit hook, Python package or image).
- **Device on the same home network** (relevant to local services that listen on ports).

## Entry points (Phase 0)
1. `git commit` / `git push` from my PC.
2. GitHub Actions runs triggered by push, pull request and manual dispatch.
3. Third-party code pulled by CI and pre-commit (actions, hooks, pip packages, container images).

## Abuse cases and controls
| # | Abuse case | Controls | Status |
|---|---|---|---|
| A1 | Secret committed by mistake | `.gitignore` (tested with `git check-ignore`); gitleaks pre-commit hook on staged changes; gitleaks full-history scan in CI; `detect-private-key` hook | In place; proven: a fake GitHub token was blocked at commit time (`github-pat`, secret redacted) and CI scans the full history |
| A2 | Malicious or hijacked upstream Action / hook / image | Actions and hooks pinned by full commit SHA, gitleaks image by digest, pip packages by exact version; ~14-day cooldown before adopting releases; Dependabot proposes updates through CI | In place (config); hash-pinned pip lockfile is a gap |
| A3 | Pull request from a fork tries to steal secrets via CI | Workflow token is `contents: read`; `persist-credentials: false`; no repository secrets exist; no `pull_request_target` trigger | In place (config) |
| A4 | Unredacted evidence or personal data published | Raw evidence folders git-ignored; commits use a GitHub noreply email; redaction checklist before every commit | Partly process-only; no automated redaction check yet (gap) |

## Known future trust boundaries (to model when the phase starts)
- **Phase 3, Kusto emulator:** Microsoft documents that it supports **no HTTPS and no Microsoft
  Entra authentication**. It must be published on `127.0.0.1` only, never `0.0.0.0` (the Learn
  example uses `-p 8080:8080`, which listens on all interfaces).
- **Phase 4, AI triage agent:** log fields are attacker-controlled input (prompt injection); the
  agent only proposes actions; evidence IDs are validated.
- **Phase 5–6, live cloud:** GitHub OIDC federation scoped to one repo/branch/environment;
  least-privilege roles; budget alerts; daily ingestion cap; no public RDP.
- **Phase 6, Logic Apps playbooks:** managed identity with minimal Graph permissions; human approval
  before disabling users or keys.

## Gaps
1. pip dependencies are pinned by version but not by hash (`--require-hashes`).
2. No automated redaction check for screenshots/exports.
3. Branch protection (required status checks) not yet configured on `main`.
4. The `.env` ignore rules are not yet verified with
   `git check-ignore -v .env .env.local .env.example`.
