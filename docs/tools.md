# Tools used in this lab

Every tool, file format and acronym, explained once in plain language, in the order it was introduced.
Format: **what it is** · analogy · **why this project uses it** · SOC / interview angle.

## Phase 0 — environment and repo

### PowerShell
Windows' command-line shell. · Texting instructions to your PC instead of clicking.
**Why:** I run lab commands here; helper scripts are `.ps1`. · Attackers love it too: encoded
PowerShell is a classic technique we detect later.

### Git Bash
A Linux-style shell for Windows that ships with Git. **Why:** runs Linux-style commands and scripts on Windows.

### winget
Windows' built-in package manager. · An app store you use by typing.
**Why:** installed Azure CLI and AWS CLI and verified each installer's hash (proof it wasn't tampered with).

### WSL2 (Windows Subsystem for Linux)
A real Linux kernel inside Windows. · A small Linux flat inside your Windows house.
**Why:** Docker needs Linux to run containers like the Kusto emulator.

### Hyper-V and VirtualBox (hypervisors)
Software that runs virtual computers (VMs). · A computer inside your computer.
**Why:** the Windows lab VM (`DaC-Win10-Endpoint`) for safe attack simulation and Velociraptor (Phase 4B).

### Git
Version control: every change is a dated, signed snapshot (a *commit*). · The incident-ticket timeline for code.
**Why:** full history of every rule and script; `git revert` rolls back a noisy rule. ·
Interview: "How do you manage detections at scale?" → detection-as-code.

### GitHub and `gh` (GitHub CLI)
GitHub hosts Git repos online and runs automation; `gh` controls it from the command line.
**Why:** public portfolio + CI; `gh` creates the repo and checks CI without clicking.

### `.gitignore` and `git check-ignore`
`.gitignore` lists files Git must never pick up; `git check-ignore -v <name>` shows which rule matches.
**Why:** keeps keys and raw evidence out of a public repo. **Lesson learned:** `#` is a comment only at
the start of a line. A trailing comment silently broke our rules, a false negative caught only by testing.
**Not a security control on its own:** `git add -f` bypasses it, and already-tracked files stay tracked.

### PEM files (`.pem`) and related key formats
PEM is a text format (Base64 between `-----BEGIN ...-----` / `-----END ...-----` lines) for
certificates (public ID card) and private keys (the secret stamp). Name comes from the failed 1990s
"Privacy-Enhanced Mail" standard. Related: `.key` (private key), `.crt`/`.cer` (certificate),
`.pfx`/`.p12` (password-protected certificate + private key bundle).
**Why we block all of them:** the extension doesn't tell you whether it's a harmless certificate or a
secret key, so deny by default. · AWS EC2 key pairs download as `.pem`; attackers add their own
certificate to an Azure service principal for persistence (one of our detections).

### Python, pip and the virtual environment (`.venv`)
Python is the project's programming language; pip installs Python packages; `.venv` is a private
Python just for this project. · A dedicated toolbox per job.
**Why:** exact, repeatable versions (`requirements-dev.txt`). Every package is someone else's code,
so it's pinned and audited (supply-chain security).

### Docker Desktop / containers
Runs containers: sealed boxes holding one program and everything it needs. · A VM is a whole house;
a container is a furnished shipping container.
**Why:** runs the Kusto emulator locally and in CI. **Known issue:** Docker Desktop on Windows can
crash after an unclean exit because of stale socket files; fix with `scripts\fix_docker_stale_sockets.ps1`.

### Azure CLI (`az`), Bicep, AWS CLI (`aws`)
Command-line control of Azure and AWS; Bicep is Microsoft's Infrastructure-as-Code language that
compiles to ARM JSON. · A recipe that produces the identical dish every time.
**Why:** the live lab is deployed and torn down by code (Phase 5–6), not by clicking.

### pre-commit
Runs checks automatically on every `git commit`. · A bouncer checking every commit at the door.
**Why:** catches secrets and broken files before they enter history. Same checks run in CI.

### ruff
Python linter and formatter (includes bandit-style security rules, `S`). · Spell- and grammar-check for code.
**Why:** readable, consistent code; flags real bugs and insecure patterns (a SAST layer).

### yamllint
Linter for YAML, the format of Sentinel rules, CI workflows and scenarios.
**Why:** in YAML, one wrong indent silently changes meaning.

### gitleaks
Scans files and git history for strings that look like secrets.
**Why:** second layer behind `.gitignore`. Runs on staged changes (pre-commit) and on full history (CI).
· Interview: "a key was committed then deleted": it's still in history; **rotate first**, then clean up.

### GitHub Actions (CI)
GitHub's automation service: on every push, a fresh machine (runner) runs our checks.
· Airport security for every change. **Why:** a red run blocks a broken rule or leaked key from merging.

### Dependabot
GitHub bot that opens pull requests when a pinned dependency has an update or a known vulnerability.
**Why:** pins stay current without trusting "latest"; each update must still pass CI.

## Phase 1 — telemetry

### Microsoft ISOC (Integrated Security Operations Center)
Sentinel's SIEM features (case management, workbooks, automation, playbooks) built into the Microsoft
Defender portal as a benefit of Microsoft 365 E5 / E7 / Defender Suite. · A gym membership that now
includes the pool: the core is included, guests (extra data) and longer locker time (retention beyond
90 days) cost extra. **Why:** a recent platform shift in Microsoft SecOps; I plan to test it on the E5
trial tenant if it qualifies (verify-first, see `docs/architecture.md`). · Note the schema split:
Sentinel's `SigninLogs` vs Defender's `EntraIdSignInEvents` for the same sign-ins.

### Kusto emulator
Microsoft's real Kusto (KQL) query engine, packaged as a Linux container that runs on my PC. ·
A flight simulator with the real cockpit. **Why:** I write and test KQL and detections for free,
offline, and later in CI. The same queries run unchanged in Sentinel. No authentication or HTTPS,
so it listens on `127.0.0.1` only (proven in `docs/threat-model.md`).

### Docker Compose (`docker-compose.yml`)
A text file that describes how to run a container: image, settings, ports, limits. · A recipe card,
so `docker compose up -d` gives everyone the exact same setup. **Why:** repeatable, reviewable in Git,
and every security setting is visible in one place.

### `scripts/kql.py`
My small helper that sends KQL to the local emulator and prints a table. Standard library only, URL
fixed to localhost. Usage: `.venv\Scripts\python scripts\kql.py --db training "SigninLogs | take 5"`.

### KQL (Kusto Query Language)
The query language of Microsoft Sentinel, Defender advanced hunting, Log Analytics and Azure Data
Explorer. Reads left to right: `Table | where … | summarize … | project …`, each `|` passing results
to the next step. · A conveyor belt of filtering and counting machines. **Why:** about 80% of a
Sentinel analyst's investigation, hunting and detection work is KQL.
