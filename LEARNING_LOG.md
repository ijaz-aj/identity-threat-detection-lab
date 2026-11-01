# Learning log

Written by me, in my own words, at the end of each session: 3–5 lines on what I learned,
what confused me, and one thing I could now explain in an interview.

<!-- Template (copy for each session):
## YYYY-MM-DD — Phase X: topic
- I learned:
- It confused me that:
- In an interview I could explain:
-->

## 2026-10-31 — Phase 0: repo, CI and secret scanning
- I learned: `.gitignore` is not a security control on its own, it only stops untracked files from
  being added. So secrets have three layers: `.gitignore`, a gitleaks pre-commit hook, and a gitleaks
  scan of the full git history in CI.
- I learned: in `.gitignore`, `#` is a comment only at the start of a line. A comment after a rule
  silently broke it, so `*.pem` keys would have been committed. `git check-ignore` caught it. Same
  lesson as a KQL rule that never fires: test the control, don't trust how it reads.
- It confused me that: a `.pem` file can hold a public certificate or a private key, and the name
  doesn't tell you which. That's why every `.pem` is blocked by default.
- In an interview I could explain: why a green CI run isn't proof (a scanner that scanned nothing
  also passes, so I checked the log said "1 commits scanned"), why Actions are pinned by commit SHA
  instead of a tag, and why a leaked key must be rotated first, because deleting it in a later commit
  doesn't remove it from history.
