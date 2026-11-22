"""Run KQL against the local Kusto emulator and print the result as a table.

Usage (from the repo root, emulator running via `docker compose up -d`):
    .venv\\Scripts\\python scripts\\kql.py "SigninLogs | take 5"
    .venv\\Scripts\\python scripts\\kql.py --file data\\samples\\password_spray_mini.kql

How it works:
- A command that starts with "." (like .create or .ingest) is a management command and
  goes to the management endpoint. Anything else is a query and goes to the query endpoint.
- In a --file, commands are separated by a blank line, and lines starting with // are comments.

Safety: the emulator has no authentication, so this script only ever talks to the
emulator on this PC (127.0.0.1). The URL is fixed in code, not taken from user input.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

EMULATOR_URL = "http://127.0.0.1:8080"
DEFAULT_DATABASE = "lab"
# Database that always exists in the emulator; used to create our own database.
SYSTEM_DATABASE = "NetDefaultDB"


def run_command(command, database):
    """Send one KQL query or management command and return the parsed JSON response."""
    is_management = command.lstrip().startswith(".")
    endpoint = "/v1/rest/mgmt" if is_management else "/v1/rest/query"
    if command.lstrip().startswith(".create database"):
        database = SYSTEM_DATABASE

    body = json.dumps({"db": database, "csl": command}).encode("utf-8")
    # ruff S310 warns that a URL could use an unexpected scheme such as file://.
    # Safe here: the URL is the fixed http://127.0.0.1 constant above, never user input.
    request = urllib.request.Request(  # noqa: S310
        EMULATOR_URL + endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return json.load(response)


def print_table(response):
    """Print the first result table as aligned columns."""
    table = response["Tables"][0]
    headers = [column["ColumnName"] for column in table["Columns"]]
    rows = [["" if value is None else str(value) for value in row] for row in table["Rows"]]

    widths = [len(header) for header in headers]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))

    print("  ".join(header.ljust(widths[i]) for i, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[i]) for i, value in enumerate(row)))
    print(f"({len(rows)} row(s))")


def read_commands(path):
    """Split a .kql file into commands: drop // comment lines, split on blank lines."""
    with open(path, encoding="utf-8") as file:
        lines = [line for line in file.read().splitlines() if not line.strip().startswith("//")]
    commands, current = [], []
    for line in lines:
        if line.strip():
            current.append(line)
        elif current:
            commands.append("\n".join(current))
            current = []
    if current:
        commands.append("\n".join(current))
    return commands


def main():
    parser = argparse.ArgumentParser(description="Run KQL against the local Kusto emulator.")
    parser.add_argument("query", nargs="?", help="A KQL query or management command")
    parser.add_argument("--file", help="A .kql file with commands separated by blank lines")
    parser.add_argument("--db", default=DEFAULT_DATABASE, help="Database name (default: lab)")
    args = parser.parse_args()

    if not args.query and not args.file:
        parser.error("give a query in quotes, or --file path/to/file.kql")

    commands = read_commands(args.file) if args.file else [args.query]
    for command in commands:
        first_line = command.splitlines()[0]
        try:
            response = run_command(command, args.db)
        except urllib.error.HTTPError as error:
            # Fail closed: show the engine's error message and stop.
            print(f"ERROR running: {first_line}\n{error.read().decode('utf-8', 'replace')}")
            sys.exit(1)
        except urllib.error.URLError:
            print("ERROR: cannot reach the emulator on 127.0.0.1:8080.")
            print("Is it running? Check with: docker compose ps")
            sys.exit(1)
        if args.file:
            print(f"\n> {first_line}")
        print_table(response)


if __name__ == "__main__":
    main()
