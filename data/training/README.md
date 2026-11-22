# KQL training dataset (synthetic)

One **synthetic** week (Mon 9 – Sun 15 Nov 2026) of a small company's security logs, with
**19 attack scenarios hidden in normal activity**. I use it to practise KQL and detection work on
the local Kusto emulator, from everyday L1 triage to senior-level hunting.

> **Not real telemetry.** IPs come from documentation ranges (RFC 5737), ASNs from the
> documentation ASN range (RFC 5398), `lab.example` is a reserved domain, and AWS account
> `111122223333` is AWS's own example number. Column names and types follow the real table
> schemas (see `docs/references.md`). Nested JSON shapes are modelled on real records and will be
> checked against live data in Phase 6. **AzureActivity operation names are UNVERIFIED** until then.

## Load it
```powershell
.venv\Scripts\python data\training\generate.py
docker compose up -d
.venv\Scripts\python scripts\kql.py --db training --file data\training\load.kql
```
Then query it: `.venv\Scripts\python scripts\kql.py --db training "SigninLogs | take 5"`

## What's inside
| Table | Rows | Normal activity included |
|---|---|---|
| `SigninLogs` | 1,871 | Office and home sign-ins, typos, MFA prompts, "keep me signed in", token refreshes, Conditional Access blocks, a colleague travelling abroad |
| `OfficeActivity` | 95 | Mailbox access, legitimate inbox rules |
| `SecurityEvent` | 201 | Normal logons, an IT inventory script |
| `AWSCloudTrail` | 87 | CI pipeline activity, admin console sign-ins with MFA |
| `AuditLogs` | 10 | New joiner, MFA registration, a business-hours role change, a normal app consent |
| `AzureActivity` | 7 | Routine VM changes |

## Scenario tiers (titles only, no spoilers)
| Tier | Who handles it | Examples of the attack types hidden here |
|---|---|---|
| 1 | Junior / L1, everyday classics | brute force, password spray, RDP brute force, sign-in from a new country, legacy authentication |
| 2 | L2 analyst | business email compromise, MFA fatigue, Office macro → encoded PowerShell, night-time role assignment, leaked cloud access key |
| 3 | Senior / modern techniques | AiTM session replay, device-code phishing, illicit OAuth consent, MFA method takeover, service-principal secrets, cloud permission enumeration, log clearing, cross-cloud pivot |

Each tier also contains **benign look-alikes** (a traveller, a conference-room device, a normal
app consent, legitimate inbox rules) so that a query that's too broad produces false positives.

`out/answer_key.csv` lists every scenario with its time window and key entities. It is git-ignored.
Check it only **after** hunting.
