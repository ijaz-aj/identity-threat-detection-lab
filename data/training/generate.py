"""Generate the KQL training dataset: one synthetic week of a small company's logs.

What it produces (in data/training/out/, which is git-ignored):
- SigninLogs.csv, AuditLogs.csv, OfficeActivity.csv, AWSCloudTrail.csv,
  SecurityEvent.csv, AzureActivity.csv  -> loaded into the emulator by load.kql
- answer_key.csv  -> which scenario happened when. Don't open it until you've hunted.

Everything is SYNTHETIC lab data:
- IPs come from documentation ranges (RFC 5737), ASNs from the documentation ASN range
  (RFC 5398), the domain lab.example is reserved, AWS account 111122223333 is AWS's
  own example account number.
- Column names and types follow the real table schemas (docs/references.md). The shape of
  nested JSON fields is modelled on real records and will be checked against live data in
  Phase 6. AzureActivity operation names are UNVERIFIED until then.

Run (from the repo root):  .venv\\Scripts\\python data\\training\\generate.py
The output is deterministic: the same seed always produces the same week.
"""

import base64
import csv
import json
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

OUT_DIR = Path(__file__).parent / "out"
SEED = 20261109
rng = random.Random(SEED)  # noqa: S311 - synthetic data, not security-sensitive randomness

WEEK_START = datetime(2026, 11, 9, tzinfo=UTC)  # Monday
DOMAIN = "lab.example"
AWS_ACCOUNT = "111122223333"
AZURE_SUB = "00000000-1111-2222-3333-444444444444"

# Office NAT addresses and the documentation ASNs used for "normal" networks.
OFFICE_IPS = [f"198.51.100.{n}" for n in range(20, 30)]
ASN_OFFICE, ASN_HOME_ISP, ASN_HOSTING = "64500", "64501", "64510"

STAFF = [
    "aarav",
    "aditi",
    "alice",
    "ananya",
    "arjun",
    "bob",
    "chen",
    "deepa",
    "divya",
    "emre",
    "farah",
    "gaurav",
    "isha",
    "kiran",
    "meera",
    "neha",
    "nikhil",
    "pooja",
    "priya",
    "rahul",
    "riya",
    "sana",
    "tara",
    "vikram",
]
ADMINS = ["it.admin1", "it.admin2"]
USERS = STAFF + ADMINS

APPS = ["Office 365 Exchange Online", "Microsoft Teams", "Office 365 SharePoint Online", "My Apps"]
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
)

# Each user gets a fixed home IP, so "normal" locations are learnable from the data.
HOME_IP = {user: f"192.0.2.{10 + i}" for i, user in enumerate(USERS)}

rows = {
    "SigninLogs": [],
    "AuditLogs": [],
    "OfficeActivity": [],
    "AWSCloudTrail": [],
    "SecurityEvent": [],
    "AzureActivity": [],
}
answer_key = []


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def at(day, hour, minute=0, second=0):
    """A UTC timestamp: `day` 0 = Monday 9 Nov 2026."""
    return WEEK_START + timedelta(days=day, hours=hour, minutes=minute, seconds=second)


def iso(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def upn(user):
    return f"{user}@{DOMAIN}"


def display(user):
    return user.replace(".", " ").title()


def new_id():
    return str(uuid.UUID(int=rng.getrandbits(128)))


def record_scenario(sid, tier, title, tables, start, end, entities):
    answer_key.append(
        {
            "ScenarioId": sid,
            "Tier": tier,
            "Title": title,
            "Tables": tables,
            "Start": iso(start),
            "End": iso(end),
            "KeyEntities": entities,
        }
    )


# Result codes used in SigninLogs (verified on Microsoft Learn; see docs/references.md).
RESULT_TEXT = {
    "0": "",
    "50126": "Error validating credentials due to invalid username or password.",
    "50053": "Account is locked because the user tried to sign in too many times.",
    "50076": "User must use multifactor authentication to access the resource.",
    "50140": "Keep me signed in interrupt.",
    "500121": "Authentication failed during strong authentication request.",
    "53003": "Access has been blocked by Conditional Access policies.",
}


def signin(
    ts,
    user,
    ip,
    location,
    result,
    *,
    asn=ASN_HOME_ISP,
    app=None,
    client="Browser",
    ua=BROWSER_UA,
    interactive=True,
    protocol="none",
    session=None,
    city=None,
):
    """Append one SigninLogs row and return its SessionId."""
    session = session or new_id()
    rows["SigninLogs"].append(
        {
            "TimeGenerated": iso(ts),
            "UserPrincipalName": upn(user),
            "UserDisplayName": display(user),
            "IPAddress": ip,
            "Location": location,
            "LocationDetails": json.dumps({"city": city or "", "countryOrRegion": location}),
            "AutonomousSystemNumber": asn,
            "AppDisplayName": app or rng.choice(APPS),
            "ClientAppUsed": client,
            "UserAgent": ua,
            "DeviceDetail": json.dumps(
                {"operatingSystem": "Windows10", "browser": "Chrome 131"}
                if client == "Browser"
                else {"operatingSystem": "", "browser": ""}
            ),
            "ResultType": result,
            "ResultDescription": RESULT_TEXT.get(result, ""),
            "IsInteractive": "true" if interactive else "false",
            "AuthenticationProtocol": protocol,
            "ConditionalAccessStatus": "failure" if result == "53003" else "success",
            "RiskLevelDuringSignIn": "none",
            "SessionId": session,
            "UniqueTokenIdentifier": new_id(),
            "CorrelationId": new_id(),
        }
    )
    return session


def audit(ts, operation, category, initiated_by, targets, *, details=None, result="success"):
    rows["AuditLogs"].append(
        {
            "TimeGenerated": iso(ts),
            "OperationName": operation,
            "ActivityDisplayName": operation,
            "Category": category,
            "Result": result,
            "ResultReason": "",
            "InitiatedBy": json.dumps(initiated_by),
            "TargetResources": json.dumps(targets),
            "AdditionalDetails": json.dumps(details or []),
            "LoggedByService": "Core Directory",
            "CorrelationId": new_id(),
        }
    )


def by_user(user, ip):
    return {"user": {"userPrincipalName": upn(user), "ipAddress": ip, "id": new_id()}}


def target_user(user, role=None):
    target = {
        "type": "User",
        "userPrincipalName": upn(user),
        "displayName": display(user),
        "modifiedProperties": [],
    }
    if role:
        target["modifiedProperties"].append(
            {"displayName": "Role.DisplayName", "oldValue": None, "newValue": json.dumps(role)}
        )
    return target


def office(ts, operation, user, ip, *, params=None, owner=None, app_id="", workload="Exchange"):
    rows["OfficeActivity"].append(
        {
            "TimeGenerated": iso(ts),
            "Operation": operation,
            "OfficeWorkload": workload,
            "UserId": upn(user) if "@" not in user else user,
            "MailboxOwnerUPN": upn(owner or user)
            if "@" not in (owner or user)
            else (owner or user),
            "ClientIP": ip,
            "Parameters": json.dumps([{"Name": k, "Value": v} for k, v in (params or {}).items()]),
            "ResultStatus": "Succeeded",
            "ExternalAccess": "false",
            "AppId": app_id,
        }
    )


def cloudtrail(
    ts,
    event,
    source,
    user,
    ip,
    *,
    key="",
    identity_type="IAMUser",
    request=None,
    response=None,
    extra=None,
    error="",
    read_only=False,
    mfa=False,
    ua="aws-cli/2.39.3",
    event_type="AwsApiCall",
    region="us-east-1",
):
    arn = (
        f"arn:aws:iam::{AWS_ACCOUNT}:root"
        if identity_type == "Root"
        else f"arn:aws:iam::{AWS_ACCOUNT}:user/{user}"
    )
    rows["AWSCloudTrail"].append(
        {
            "TimeGenerated": iso(ts),
            "EventName": event,
            "EventSource": source,
            "EventTypeName": event_type,
            "AWSRegion": region,
            "SourceIpAddress": ip,
            "UserAgent": ua,
            "UserIdentityType": identity_type,
            "UserIdentityUserName": "" if identity_type == "Root" else user,
            "UserIdentityArn": arn,
            "UserIdentityAccessKeyId": key,
            "UserIdentityAccountId": AWS_ACCOUNT,
            "SessionMfaAuthenticated": "true" if mfa else "false",
            "ErrorCode": error,
            "ErrorMessage": "User is not authorized to perform this operation" if error else "",
            "RequestParameters": json.dumps(request) if request else "",
            "ResponseElements": json.dumps(response) if response else "",
            "AdditionalEventData": json.dumps(extra) if extra else "",
            "ReadOnly": "true" if read_only else "false",
            "ManagementEvent": "true",
            "RecipientAccountId": AWS_ACCOUNT,
        }
    )


# Windows event summaries (verified: Microsoft "Appendix L: Events to Monitor").
WIN_ACTIVITY = {
    4624: "An account was successfully logged on.",
    4625: "An account failed to log on.",
    4688: "A new process has been created.",
    4698: "A scheduled task was created.",
    4720: "A user account was created.",
    4732: "A member was added to a security-enabled local group.",
    1102: "The audit log was cleared.",
}
LOGON_TYPE_NAME = {2: "Interactive", 3: "Network", 10: "RemoteInteractive"}


def winevent(
    ts,
    computer,
    event_id,
    *,
    account="",
    target_user="",
    subject_user="",
    logon_type=None,
    ip="",
    workstation="",
    process="",
    parent="",
    command="",
    member="",
):
    rows["SecurityEvent"].append(
        {
            "TimeGenerated": iso(ts),
            "Computer": computer,
            "EventID": event_id,
            "Activity": f"{event_id} - {WIN_ACTIVITY[event_id]}",
            "Account": account,
            "AccountType": "User",
            "LogonType": logon_type if logon_type is not None else "",
            "LogonTypeName": LOGON_TYPE_NAME.get(logon_type, ""),
            "IpAddress": ip,
            "WorkstationName": workstation,
            "TargetUserName": target_user,
            "SubjectUserName": subject_user,
            "NewProcessName": process,
            "ParentProcessName": parent,
            "CommandLine": command,
            "MemberName": member,
        }
    )


def azure(
    ts,
    operation,
    caller,
    ip,
    resource_group,
    *,
    status="Succeeded",
    properties=None,
    category="Administrative",
):
    rows["AzureActivity"].append(
        {
            "TimeGenerated": iso(ts),
            "OperationNameValue": operation,
            "ActivityStatusValue": status,
            "Caller": upn(caller),
            "CallerIpAddress": ip,
            "CategoryValue": category,
            "ResourceGroup": resource_group,
            "ResourceProviderValue": operation.split("/")[0],
            "SubscriptionId": AZURE_SUB,
            "Properties_d": json.dumps(properties or {}),
            "Level": "Informational",
        }
    )


# ---------------------------------------------------------------------------
# Normal business activity (the noise every real SOC has to see through)
# ---------------------------------------------------------------------------
def baseline():
    for day in range(7):
        weekend = day >= 5
        for user in USERS:
            if weekend and rng.random() < 0.8:
                continue
            # Working hours 09:00-19:00 IST = 03:30-13:30 UTC.
            for _ in range(rng.randint(2, 5)):
                ts = at(day, rng.randint(3, 13), rng.randint(0, 59), rng.randint(0, 59))
                at_office = not weekend and rng.random() < 0.7
                ip = rng.choice(OFFICE_IPS) if at_office else HOME_IP[user]
                asn = ASN_OFFICE if at_office else ASN_HOME_ISP
                city = "Bengaluru"
                if rng.random() < 0.05:  # typo, then success: benign look-alike of brute force
                    signin(ts, user, ip, "IN", "50126", asn=asn, city=city)
                    ts += timedelta(seconds=rng.randint(10, 40))
                if rng.random() < 0.15:  # normal MFA prompt
                    signin(ts, user, ip, "IN", "50076", asn=asn, city=city)
                    ts += timedelta(seconds=rng.randint(5, 20))
                session = signin(ts, user, ip, "IN", "0", asn=asn, city=city)
                if rng.random() < 0.2:
                    signin(ts + timedelta(seconds=3), user, ip, "IN", "50140", asn=asn, city=city)
                # Token refreshes later in the same session: non-interactive, same IP.
                for k in range(rng.randint(1, 3)):
                    signin(
                        ts + timedelta(minutes=20 * (k + 1)),
                        user,
                        ip,
                        "IN",
                        "0",
                        asn=asn,
                        client="Mobile Apps and Desktop clients",
                        interactive=False,
                        session=session,
                        city=city,
                    )
            # Everyday mailbox activity, including a few legitimate inbox rules.
            if not weekend and rng.random() < 0.6:
                office(
                    at(day, rng.randint(4, 12), rng.randint(0, 59)),
                    "MailItemsAccessed",
                    user,
                    rng.choice(OFFICE_IPS),
                )
        if not weekend:
            # A Conditional Access block on an unmanaged device now and then.
            user = rng.choice(STAFF)
            signin(at(day, 6, rng.randint(0, 59)), user, HOME_IP[user], "IN", "53003")

    # Benign look-alikes the analyst must not over-alert on.
    office(
        at(1, 5, 12),
        "New-InboxRule",
        "bob",
        "198.51.100.21",
        params={
            "Name": "Vendor newsletters",
            "From": "news@vendor.example",
            "MoveToFolder": "Newsletters",
        },
    )
    office(
        at(3, 8, 40),
        "New-InboxRule",
        "neha",
        "198.51.100.22",
        params={
            "Name": "Project Falcon",
            "SubjectContainsWords": "Falcon",
            "MoveToFolder": "Projects",
        },
    )
    # Meera travels to Singapore from Wednesday: new country, but consistent and benign.
    for day in range(2, 5):
        for hour in (2, 6, 10):
            signin(
                at(day, hour, rng.randint(0, 59)),
                "meera",
                "192.0.2.250",
                "SG",
                "0",
                asn=ASN_HOME_ISP,
                city="Singapore",
            )
    # IT admin does legitimate admin work in business hours.
    audit(
        at(1, 6, 15),
        "Add user",
        "UserManagement",
        by_user("it.admin1", "198.51.100.20"),
        [target_user("new.joiner")],
    )
    audit(
        at(1, 6, 25),
        "User registered security info",
        "UserManagement",
        by_user("new.joiner", "198.51.100.20"),
        [target_user("new.joiner")],
    )
    audit(
        at(2, 7, 5),
        "Add member to role",
        "RoleManagement",
        by_user("it.admin1", "198.51.100.20"),
        [target_user("aarav", role="User Administrator")],
    )
    audit(
        at(3, 9, 30),
        "Consent to application",
        "ApplicationManagement",
        by_user("tara", "198.51.100.24"),
        [
            {
                "type": "ServicePrincipal",
                "displayName": "Zoom",
                "id": new_id(),
                "modifiedProperties": [
                    {
                        "displayName": "ConsentAction.Permissions",
                        "newValue": json.dumps("User.Read"),
                    }
                ],
            }
        ],
    )
    # Conference-room device signing in with device code from the office: benign.
    signin(
        at(2, 4, 10),
        "it.admin2",
        "198.51.100.25",
        "IN",
        "0",
        asn=ASN_OFFICE,
        protocol="deviceCode",
        app="Microsoft Teams",
        client="Mobile Apps and Desktop clients",
    )

    # Windows: normal logons and IT scripts on the file server and workstations.
    for day in range(7):
        for host in ("SRV-FILE01", "WKS-014", "WKS-022"):
            for _ in range(rng.randint(3, 8)):
                user = rng.choice(STAFF)
                winevent(
                    at(day, rng.randint(3, 13), rng.randint(0, 59)),
                    host,
                    4624,
                    account=f"LAB\\{user}",
                    target_user=user,
                    logon_type=rng.choice([2, 3]),
                    ip=rng.choice(OFFICE_IPS),
                    workstation=host,
                )
            winevent(
                at(day, 4, 0),
                host,
                4688,
                account="LAB\\it.admin1",
                subject_user="it.admin1",
                process="C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                parent="C:\\Windows\\System32\\svchost.exe",
                command="powershell.exe -File C:\\Scripts\\inventory.ps1",
            )

    # AWS: the CI pipeline and admins doing normal work.
    for day in range(5):
        for hour in (5, 9, 12):
            cloudtrail(
                at(day, hour, rng.randint(0, 59)),
                "ListBuckets",
                "s3.amazonaws.com",
                "ci-deployer",
                "198.51.100.200",
                key="AKIAEXAMPLECI00001",
                read_only=True,
                ua="aws-sdk-python/1.35",
            )
            cloudtrail(
                at(day, hour, rng.randint(0, 59)),
                "PutBucketTagging",
                "s3.amazonaws.com",
                "ci-deployer",
                "198.51.100.200",
                key="AKIAEXAMPLECI00001",
                request={"bucketName": "lab-app-artifacts"},
                ua="aws-sdk-python/1.35",
            )
        cloudtrail(
            at(day, 6, 2),
            "ConsoleLogin",
            "signin.amazonaws.com",
            "it.admin1",
            "198.51.100.20",
            response={"ConsoleLogin": "Success"},
            extra={"MFAUsed": "Yes"},
            mfa=True,
            ua=BROWSER_UA,
            event_type="AwsConsoleSignIn",
        )
        cloudtrail(
            at(day, 6, 10),
            "ListUsers",
            "iam.amazonaws.com",
            "it.admin1",
            "198.51.100.20",
            read_only=True,
            mfa=True,
            ua=BROWSER_UA,
        )

    # Azure: routine admin changes.
    for day in range(5):
        azure(
            at(day, 7, rng.randint(0, 59)),
            "Microsoft.Compute/virtualMachines/write",
            "it.admin1",
            "198.51.100.20",
            "rg-itd-lab",
        )


# ---------------------------------------------------------------------------
# Attack scenarios: Tier 1 (junior, everyday), Tier 2 (L2), Tier 3 (senior, modern)
# ---------------------------------------------------------------------------
def s01_brute_force():
    start = at(0, 21, 3)
    ts = start
    for _ in range(40):
        signin(
            ts,
            "it.admin2",
            "203.0.113.11",
            "RU",
            "50126",
            asn=ASN_HOSTING,
            city="Moscow",
            ua="python-requests/2.32",
        )
        ts += timedelta(seconds=rng.randint(5, 12))
    for _ in range(3):
        signin(
            ts,
            "it.admin2",
            "203.0.113.11",
            "RU",
            "50053",
            asn=ASN_HOSTING,
            city="Moscow",
            ua="python-requests/2.32",
        )
        ts += timedelta(seconds=20)
    record_scenario(
        "S01",
        1,
        "Brute force against one admin account",
        "SigninLogs",
        start,
        ts,
        "it.admin2; 203.0.113.11",
    )


def s02_password_spray():
    start = at(1, 8, 0)
    ts = start
    targets = [u for u in STAFF if u not in ("divya", "meera")]
    rng.shuffle(targets)
    for user in targets[:16]:
        signin(ts, user, "203.0.113.50", "NL", "50126", asn=ASN_HOSTING, city="Amsterdam")
        ts += timedelta(minutes=rng.randint(5, 9))
    signin(ts, "divya", "203.0.113.50", "NL", "0", asn=ASN_HOSTING, city="Amsterdam")
    divya_session_time = ts
    ts += timedelta(minutes=6)
    signin(ts, targets[16], "203.0.113.50", "NL", "50053", asn=ASN_HOSTING, city="Amsterdam")
    record_scenario(
        "S02",
        1,
        "Low-and-slow password spray with one success",
        "SigninLogs",
        start,
        ts,
        "203.0.113.50; divya (compromised)",
    )
    return divya_session_time


def s03_rdp_brute_force_and_s17_log_clear():
    start = at(2, 19, 30)
    ts = start
    for name in ["administrator", "admin", "user", "test", "backup", "scanner"] * 10:
        winevent(
            ts,
            "SRV-FILE01",
            4625,
            account=f"SRV-FILE01\\{name}",
            target_user=name,
            logon_type=10,
            ip="203.0.113.23",
            workstation="kali",
        )
        ts += timedelta(seconds=rng.randint(2, 6))
    winevent(
        ts,
        "SRV-FILE01",
        4624,
        account="SRV-FILE01\\administrator",
        target_user="administrator",
        logon_type=10,
        ip="203.0.113.23",
        workstation="kali",
    )
    record_scenario(
        "S03",
        1,
        "RDP brute force then successful remote logon",
        "SecurityEvent",
        start,
        ts,
        "SRV-FILE01; 203.0.113.23; administrator",
    )
    clear_ts = ts + timedelta(minutes=18)
    winevent(
        clear_ts,
        "SRV-FILE01",
        1102,
        account="SRV-FILE01\\administrator",
        subject_user="administrator",
    )
    record_scenario(
        "S17",
        3,
        "Security event log cleared after intrusion",
        "SecurityEvent",
        clear_ts,
        clear_ts,
        "SRV-FILE01; administrator",
    )


def s04_impossible_new_country():
    ts = at(3, 20, 10)  # 01:40 IST, when Kiran is normally offline
    signin(
        ts,
        "kiran",
        "203.0.113.140",
        "BR",
        "0",
        asn=ASN_HOSTING,
        city="Sao Paulo",
        ua="Mozilla/5.0 (X11; Linux x86_64) Firefox/118.0",
    )
    record_scenario(
        "S04",
        1,
        "Successful sign-in from a never-seen country at night (Meera's SG travel "
        "is the benign look-alike)",
        "SigninLogs",
        ts,
        ts,
        "kiran; 203.0.113.140; BR",
    )


def s05_legacy_auth():
    start = at(4, 18, 0)
    ts = start
    for user in ("gaurav", "isha", "nikhil"):
        for _ in range(4):
            signin(
                ts,
                user,
                "203.0.113.77",
                "VN",
                "50126",
                asn=ASN_HOSTING,
                client="IMAP",
                ua="",
                app="Office 365 Exchange Online",
            )
            ts += timedelta(seconds=30)
    signin(
        ts,
        "nikhil",
        "203.0.113.77",
        "VN",
        "0",
        asn=ASN_HOSTING,
        client="IMAP",
        ua="",
        app="Office 365 Exchange Online",
    )
    record_scenario(
        "S05",
        1,
        "Legacy authentication (IMAP) attempts bypassing MFA, one success",
        "SigninLogs",
        start,
        ts,
        "203.0.113.77; nikhil",
    )


def s06_bec_chain(after):
    ts = after + timedelta(minutes=3)
    office(ts, "MailItemsAccessed", "divya", "203.0.113.50")
    office(
        ts + timedelta(minutes=2),
        "New-InboxRule",
        "divya",
        "203.0.113.50",
        params={
            "Name": ".",
            "SubjectOrBodyContainsWords": "invoice;payment;bank;hacked",
            "MoveToFolder": "RSS Feeds",
            "MarkAsRead": "True",
            "StopProcessingRules": "True",
        },
    )
    office(
        ts + timedelta(minutes=4),
        "New-InboxRule",
        "divya",
        "203.0.113.50",
        params={"Name": "sync", "ForwardTo": "d.accounts@freemail.example"},
    )
    office(
        ts + timedelta(minutes=30),
        "Send",
        "divya",
        "203.0.113.50",
        params={"Subject": "Updated bank details for invoice 4471"},
    )
    record_scenario(
        "S06",
        2,
        "Business email compromise: mail access, hiding rule, external forward",
        "OfficeActivity",
        ts,
        ts + timedelta(minutes=30),
        "divya; 203.0.113.50",
    )


def s07_mfa_fatigue_and_s14_mfa_registration():
    start = at(4, 20, 30)  # 02:00 IST
    ts = start
    session = new_id()
    for _ in range(12):
        signin(
            ts,
            "rahul",
            "203.0.113.88",
            "US",
            "500121",
            asn=ASN_HOSTING,
            session=session,
            city="Ashburn",
        )
        ts += timedelta(minutes=1, seconds=rng.randint(0, 20))
    signin(ts, "rahul", "203.0.113.88", "US", "0", asn=ASN_HOSTING, session=session, city="Ashburn")
    record_scenario(
        "S07",
        2,
        "MFA fatigue: repeated push denials then approval at night",
        "SigninLogs",
        start,
        ts,
        "rahul; 203.0.113.88",
    )
    reg = ts + timedelta(minutes=4)
    audit(
        reg,
        "User registered security info",
        "UserManagement",
        by_user("rahul", "203.0.113.88"),
        [target_user("rahul")],
        details=[{"key": "Method", "value": "Authenticator app"}],
    )
    record_scenario(
        "S14",
        3,
        "Attacker registers their own MFA method for persistence",
        "AuditLogs",
        reg,
        reg,
        "rahul; 203.0.113.88",
    )


def s08_encoded_powershell():
    start = at(5, 10, 12)
    # A harmless placeholder command, base64-encoded the way PowerShell's -enc flag expects.
    payload = base64.b64encode("Write-Output 'lab-simulation'".encode("utf-16-le")).decode()
    winevent(
        start,
        "WKS-022",
        4688,
        account="LAB\\sana",
        subject_user="sana",
        process="C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
        parent="C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
        command=f"powershell.exe -nop -w hidden -enc {payload}",
    )
    winevent(
        start + timedelta(minutes=2),
        "WKS-022",
        4720,
        account="LAB\\sana",
        subject_user="sana",
        target_user="support",
    )
    winevent(
        start + timedelta(minutes=3),
        "WKS-022",
        4732,
        account="LAB\\sana",
        subject_user="sana",
        target_user="Administrators",
        member="WKS-022\\support",
    )
    winevent(
        start + timedelta(minutes=5),
        "WKS-022",
        4698,
        account="LAB\\sana",
        subject_user="sana",
        target_user="\\Microsoft\\Windows\\UpdateCheck",
    )
    record_scenario(
        "S08",
        2,
        "Office macro spawns encoded PowerShell, new local admin, scheduled task",
        "SecurityEvent",
        start,
        start + timedelta(minutes=5),
        "WKS-022; sana; support; WINWORD.EXE",
    )


def s09_night_role_assignment():
    ts = at(1, 16, 40)  # 22:10 IST, done from Divya's compromised account
    audit(
        ts,
        "Add user",
        "UserManagement",
        by_user("divya", "203.0.113.50"),
        [target_user("svc-backup")],
    )
    audit(
        ts + timedelta(minutes=3),
        "Add member to role",
        "RoleManagement",
        by_user("divya", "203.0.113.50"),
        [target_user("svc-backup", role="Global Administrator")],
    )
    record_scenario(
        "S09",
        2,
        "New account made Global Administrator at night by a compromised user",
        "AuditLogs",
        ts,
        ts + timedelta(minutes=3),
        "divya; svc-backup; 203.0.113.50",
    )


def s10_aws_leaked_key():
    start = at(3, 4, 2)
    key, ip = "AKIAEXAMPLECI00001", "203.0.113.99"
    ua = "python-requests/2.32"
    steps = [
        (0, "ListUsers", "iam.amazonaws.com", {}, True),
        (1, "ListBuckets", "s3.amazonaws.com", {}, True),
        (3, "CreateUser", "iam.amazonaws.com", {"userName": "backup-svc"}, False),
        (4, "CreateLoginProfile", "iam.amazonaws.com", {"userName": "backup-svc"}, False),
        (5, "CreateAccessKey", "iam.amazonaws.com", {"userName": "backup-svc"}, False),
        (
            6,
            "AttachUserPolicy",
            "iam.amazonaws.com",
            {"userName": "backup-svc", "policyArn": "arn:aws:iam::aws:policy/AdministratorAccess"},
            False,
        ),
    ]
    for minute, event, source, request, read_only in steps:
        cloudtrail(
            start + timedelta(minutes=minute),
            event,
            source,
            "ci-deployer",
            ip,
            key=key,
            request=request or None,
            read_only=read_only,
            ua=ua,
        )
    later = start + timedelta(minutes=9)
    cloudtrail(
        later,
        "DeleteBucketPublicAccessBlock",
        "s3.amazonaws.com",
        "backup-svc",
        ip,
        key="AKIAEXAMPLEBK00002",
        request={"bucketName": "lab-finance-reports"},
        ua=ua,
    )
    cloudtrail(
        later + timedelta(minutes=1),
        "PutBucketPolicy",
        "s3.amazonaws.com",
        "backup-svc",
        ip,
        key="AKIAEXAMPLEBK00002",
        request={
            "bucketName": "lab-finance-reports",
            "bucketPolicy": {
                "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject"}]
            },
        },
        ua=ua,
    )
    cloudtrail(
        later + timedelta(minutes=2),
        "StopLogging",
        "cloudtrail.amazonaws.com",
        "backup-svc",
        ip,
        key="AKIAEXAMPLEBK00002",
        request={"name": "lab-trail"},
        ua=ua,
    )
    record_scenario(
        "S10",
        2,
        "Leaked CI key: discovery, backdoor admin user, public bucket, logging stopped",
        "AWSCloudTrail",
        start,
        later + timedelta(minutes=2),
        "ci-deployer; AKIAEXAMPLECI00001; backup-svc; 203.0.113.99",
    )


def s11_aitm_token_replay():
    login = at(2, 5, 2)
    signin(login, "ananya", HOME_IP["ananya"], "IN", "50076", city="Bengaluru")
    session = signin(
        login + timedelta(seconds=15), "ananya", HOME_IP["ananya"], "IN", "0", city="Bengaluru"
    )
    replay = login + timedelta(minutes=7)
    for k in range(4):
        signin(
            replay + timedelta(minutes=3 * k),
            "ananya",
            "203.0.113.160",
            "US",
            "0",
            asn=ASN_HOSTING,
            interactive=False,
            session=session,
            client="Mobile Apps and Desktop clients",
            ua="axios/1.7.7",
            app="Office 365 Exchange Online",
            city="Ashburn",
        )
    office(replay + timedelta(minutes=2), "MailItemsAccessed", "ananya", "203.0.113.160")
    office(
        replay + timedelta(minutes=5),
        "New-InboxRule",
        "ananya",
        "203.0.113.160",
        params={"Name": "..", "From": "security@lab.example", "DeleteMessage": "True"},
    )
    record_scenario(
        "S11",
        3,
        "AiTM: stolen session replayed from a hosting network minutes after a real MFA sign-in",
        "SigninLogs, OfficeActivity",
        login,
        replay + timedelta(minutes=9),
        "ananya; SessionId reused; 203.0.113.160",
    )


def s12_device_code_phishing():
    ts = at(5, 9, 47)
    signin(
        ts,
        "vikram",
        "203.0.113.171",
        "DE",
        "0",
        asn=ASN_HOSTING,
        protocol="deviceCode",
        app="Office 365 Exchange Online",
        client="Mobile Apps and Desktop clients",
        ua="Mozilla/5.0 (Windows NT 10.0) PowerShell/7.4",
        city="Frankfurt",
    )
    record_scenario(
        "S12",
        3,
        "Device-code phishing: deviceCode sign-in completed from a hosting IP "
        "(office conference-room device is the benign look-alike)",
        "SigninLogs",
        ts,
        ts,
        "vikram; 203.0.113.171",
    )


def s13_oauth_consent():
    ts = at(4, 11, 20)
    app_id = "a1b2c3d4-0000-4000-8000-00000000c0de"
    audit(
        ts,
        "Consent to application",
        "ApplicationManagement",
        by_user("pooja", HOME_IP["pooja"]),
        [
            {
                "type": "ServicePrincipal",
                "displayName": "Mail Archive Pro",
                "id": app_id,
                "modifiedProperties": [
                    {
                        "displayName": "ConsentAction.Permissions",
                        "newValue": json.dumps("Mail.Read Mail.Send offline_access"),
                    }
                ],
            }
        ],
    )
    audit(
        ts + timedelta(seconds=5),
        "Add delegated permission grant",
        "ApplicationManagement",
        by_user("pooja", HOME_IP["pooja"]),
        [
            {
                "type": "ServicePrincipal",
                "displayName": "Mail Archive Pro",
                "id": app_id,
                "modifiedProperties": [],
            }
        ],
    )
    for k in range(10):
        office(
            ts + timedelta(hours=1 + k),
            "MailItemsAccessed",
            "pooja",
            "203.0.113.180",
            app_id=app_id,
        )
    record_scenario(
        "S13",
        3,
        "Illicit OAuth consent: app reads mailbox for hours (Zoom consent is the "
        "benign look-alike)",
        "AuditLogs, OfficeActivity",
        ts,
        ts + timedelta(hours=10),
        "pooja; Mail Archive Pro; 203.0.113.180",
    )


def s15_service_principal_credential():
    ts = at(1, 17, 5)
    audit(
        ts,
        "Add service principal credentials",
        "ApplicationManagement",
        by_user("divya", "203.0.113.50"),
        [
            {
                "type": "ServicePrincipal",
                "displayName": "HR-Sync",
                "id": new_id(),
                "modifiedProperties": [
                    {"displayName": "KeyDescription", "newValue": json.dumps("[KeyType=Password]")}
                ],
            }
        ],
    )
    record_scenario(
        "S15",
        3,
        "New secret added to an app's service principal from the attacker IP",
        "AuditLogs",
        ts,
        ts,
        "HR-Sync; divya; 203.0.113.50",
    )


def s16_aws_permission_enumeration():
    start = at(5, 2, 0)
    ts = start
    calls = [
        ("ListUsers", "iam"),
        ("ListRoles", "iam"),
        ("ListAccessKeys", "iam"),
        ("GetAccountAuthorizationDetails", "iam"),
        ("ListBuckets", "s3"),
        ("GetBucketPolicy", "s3"),
        ("GetBucketAcl", "s3"),
        ("DescribeTrails", "cloudtrail"),
        ("GetTrailStatus", "cloudtrail"),
    ]
    for _ in range(4):
        for event, service in calls:
            cloudtrail(
                ts,
                event,
                f"{service}.amazonaws.com",
                "dev-intern",
                "203.0.113.201",
                key="AKIAEXAMPLEDV00003",
                error="AccessDenied",
                read_only=True,
                ua="pacu/1.6",
            )
            ts += timedelta(seconds=rng.randint(2, 8))
    record_scenario(
        "S16",
        3,
        "Permission enumeration: burst of AccessDenied across services from one key",
        "AWSCloudTrail",
        start,
        ts,
        "dev-intern; AKIAEXAMPLEDV00003; 203.0.113.201",
    )


def s18_aws_root_and_azure_backdoor():
    ts = at(6, 18, 40)
    cloudtrail(
        ts,
        "ConsoleLogin",
        "signin.amazonaws.com",
        "",
        "203.0.113.190",
        identity_type="Root",
        response={"ConsoleLogin": "Success"},
        extra={"MFAUsed": "No"},
        ua=BROWSER_UA,
        event_type="AwsConsoleSignIn",
    )
    cloudtrail(
        ts + timedelta(minutes=2),
        "CreateAccessKey",
        "iam.amazonaws.com",
        "",
        "203.0.113.190",
        identity_type="Root",
        ua=BROWSER_UA,
    )
    record_scenario(
        "S18",
        3,
        "AWS root console sign-in without MFA, then a root access key created",
        "AWSCloudTrail",
        ts,
        ts + timedelta(minutes=2),
        "Root; 203.0.113.190",
    )
    az = at(1, 17, 20)
    azure(
        az,
        "Microsoft.Authorization/roleAssignments/write",
        "divya",
        "203.0.113.50",
        "rg-itd-lab",
        properties={"roleDefinitionName": "Owner", "principalName": "svc-backup"},
    )
    azure(
        az + timedelta(minutes=4),
        "Microsoft.Network/networkSecurityGroups/securityRules/write",
        "divya",
        "203.0.113.50",
        "rg-itd-lab",
        properties={
            "ruleName": "allow-rdp",
            "destinationPortRange": "3389",
            "sourceAddressPrefix": "*",
        },
    )
    record_scenario(
        "S19",
        3,
        "Cross-cloud pivot: compromised Entra user grants Owner and opens RDP to the "
        "internet in Azure",
        "AzureActivity",
        az,
        az + timedelta(minutes=4),
        "divya; svc-backup; 203.0.113.50",
    )


# ---------------------------------------------------------------------------
def write_outputs():
    OUT_DIR.mkdir(exist_ok=True)
    for table, table_rows in rows.items():
        table_rows.sort(key=lambda row: row["TimeGenerated"])
        with open(OUT_DIR / f"{table}.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(table_rows[0].keys()))
            writer.writeheader()
            writer.writerows(table_rows)
        print(f"{table:15} {len(table_rows):6} rows")
    with open(OUT_DIR / "answer_key.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(answer_key[0].keys()))
        writer.writeheader()
        writer.writerows(sorted(answer_key, key=lambda row: row["ScenarioId"]))
    print(f"{'answer_key':15} {len(answer_key):6} scenarios")


def main():
    baseline()
    s01_brute_force()
    spray_success = s02_password_spray()
    s03_rdp_brute_force_and_s17_log_clear()
    s04_impossible_new_country()
    s05_legacy_auth()
    s06_bec_chain(spray_success)
    s07_mfa_fatigue_and_s14_mfa_registration()
    s08_encoded_powershell()
    s09_night_role_assignment()
    s10_aws_leaked_key()
    s11_aitm_token_replay()
    s12_device_code_phishing()
    s13_oauth_consent()
    s15_service_principal_credential()
    s16_aws_permission_enumeration()
    s18_aws_root_and_azure_backdoor()
    write_outputs()


if __name__ == "__main__":
    main()
