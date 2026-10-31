# Architecture and design reasoning

_Diagrams are added in Phase 2 (local CI path) and Phase 5 (live Sentinel path)._

## Two paths, one rule set
1. **Local / CI path (permanent):** detection YAML → pytest → Kusto emulator (the real Kusto query
   engine in a Linux container) → precision/recall report. Runs on every push in GitHub Actions and
   keeps working after the cloud lab is torn down.
2. **Live path (30-day sprint):** the same detection YAML → GitHub Actions deploy (OIDC) →
   Microsoft Sentinel workspace, managed in the Microsoft Defender portal → real incidents from
   attacks against my own lab tenant and AWS account.

## Why this design
- **Market fit:** Bengaluru SOC L2 / detection-engineering job ads repeatedly ask for Microsoft
  Sentinel and KQL (detection, hunting, tuning), the Defender suite, SOAR playbooks, false-positive
  reduction and multi-cloud log monitoring.
- **Identity and cloud first:** identity and cloud attacks dominate modern incident response; the
  companion repo `detection-as-code` already covers Windows endpoint (Sigma/Elastic), so this one
  deliberately does not duplicate it.
- **Detection engineering as the core skill**, and **validating AI output** as an emerging analyst skill.
- **Defender portal, not the old Azure-portal experience:** new Sentinel workspaces are onboarded to
  the Defender portal (to be verified and cited in `docs/references.md` in Phase 5).
- **Build before the clock starts:** free trials last about 30 days, so rules, tests, IaC and the
  agent are built and tested locally first. The sprint is spent on operations, not debugging YAML.
- **Zero budget:** every service stays within free accounts, trials or credits; teardown is one
  resource-group delete plus one AWS stack delete.

## Platform decisions
| Decision | Choice | Why | Date |
|---|---|---|---|
| Second SOAR | **Shuffle** (Docker) | Splunk SOAR evaluation needs 4 cores, 8 GB RAM minimum (16 GB recommended) and **500 GB disk**; this PC has 15.3 GB RAM total and ~44 GB free disk. See references. | 2026-10-31 |
| Local query engine | Kusto emulator (Linux container) | Same engine as Azure Data Explorer; free; runs in CI. Differences from Sentinel are documented per rule in Phase 2. | 2026-10-31 |
| Supply chain | Pin by SHA/digest/exact version; ~14-day cooldown; Dependabot | A moved tag or a just-published malicious release can't silently enter CI. | 2026-10-31 |
