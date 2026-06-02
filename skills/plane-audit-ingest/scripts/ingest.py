#!/usr/bin/env python3
"""Parse an audit REPORT.md → audit-scoped work-item files + INGEST.md.

Audit-scoped: writes to <audit-dir>/work-items/, NOT to the project
pool. Promotion is the separate `plane-audit-promote` skill.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "lib"))
from plane_schema import (
    SEVERITY_TO_PRIORITY,
    WorkItem,
    audit_work_item_path,
    now_iso,
)


# --- audit-name → id-prefix --------------------------------------------

AUDIT_PREFIX = {
    "apple-security":         "SEC",
    "apple-performance":      "PERF",
    "apple-accessibility":    "A11Y",
    "apple-architecture":     "ARCH",
    "apple-localization":     "LOC",
    "apple-design":           "DSGN",
    "apple-adaptivity":       "ADAPT",
    "apple-testing":          "TEST",
    "apple-persistence":      "PERS",
    "apple-privacy":          "PRIV",
    "apple-app-store-review": "ASR",
}


# --- section header → severity -----------------------------------------

SECTION_SEVERITY = [
    (re.compile(r"^###\s+Immediate Action", re.IGNORECASE), "critical"),
    (re.compile(r"^###\s+P0\b",             re.IGNORECASE), "high"),
    (re.compile(r"^###\s+P1\b",             re.IGNORECASE), "medium"),
    (re.compile(r"^###\s+P2\b",             re.IGNORECASE), "low"),
    (re.compile(r"^###\s+Deferred",         re.IGNORECASE), "informational"),
    (re.compile(r"^###\s+Informational",    re.IGNORECASE), "informational"),
]


# --- regexes for parsing -----------------------------------------------

TASK_HEADER_RE = re.compile(
    r"^\*\*Task:\s*(?P<id>[A-Z]\d{1,4})\s*[—–-]\s*"
    r"(?:(?P<category>[^—–\-\n]+?)\s*[—–-]\s*)?"
    r"(?P<title>.+?)\*\*\s*$"
)

# Match a "- Field: value" or "- **Field**: value" bullet line.
FIELD_RE = re.compile(
    r"^[-*]\s+\*{0,2}(?P<field>[A-Za-z][\w /]+?)\*{0,2}\s*:\s*(?P<value>.*?)\s*$"
)


# --- parser ------------------------------------------------------------

@dataclass
class ParsedFinding:
    audit_internal_id: str        # e.g. "S001"
    category: str                 # e.g. "Entitlements" (may be "")
    title: str                    # e.g. "No .entitlements file on disk; ..."
    severity: str                 # "critical" | "high" | "medium" | "low" | "informational"
    fields: dict[str, str]        # location/cwe/platform/verification/issue/remediation/verification step/...
    raw_block: str                # full text including header + bullets, for the description fallback


def _classify_section(line: str) -> str | None:
    for pat, sev in SECTION_SEVERITY:
        if pat.match(line):
            return sev
    return None


def parse_report(text: str) -> list[ParsedFinding]:
    """Walk REPORT.md, emit a ParsedFinding per `**Task: ...**` block."""
    lines = text.splitlines()
    current_severity: str | None = None
    findings: list[ParsedFinding] = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # New ### section — update current severity.
        if line.startswith("### "):
            sev = _classify_section(line)
            if sev:
                current_severity = sev
            else:
                # Any other ### header (e.g. "### Audit Summary") clears
                # severity so stray Task lines outside the tier sections
                # don't pick up the previous severity by accident.
                current_severity = None
            i += 1
            continue

        # Higher-level ## header also clears severity (end of the
        # Implementation Plan section).
        if line.startswith("## ") and current_severity is not None:
            current_severity = None
            i += 1
            continue

        m = TASK_HEADER_RE.match(line)
        if m and current_severity:
            # Parse the bullet fields until next blank-line-followed-by-non-bullet,
            # next Task header, or new ## / ### section.
            start = i
            i += 1
            fields: dict[str, str] = {}
            current_field: str | None = None
            current_buf: list[str] = []
            while i < len(lines):
                nxt = lines[i]
                if nxt.startswith("### ") or nxt.startswith("## "):
                    break
                if TASK_HEADER_RE.match(nxt):
                    break
                fm = FIELD_RE.match(nxt)
                if fm:
                    # Flush prior field.
                    if current_field is not None:
                        fields[current_field] = "\n".join(current_buf).strip()
                    current_field = fm.group("field").strip().lower()
                    current_buf = [fm.group("value")]
                elif current_field is not None:
                    # Continuation of the prior field (indented or wrapped).
                    if nxt.strip() == "":
                        current_buf.append("")
                    else:
                        current_buf.append(nxt.strip())
                i += 1
            if current_field is not None:
                fields[current_field] = "\n".join(current_buf).strip()

            raw_block = "\n".join(lines[start:i]).strip()
            findings.append(ParsedFinding(
                audit_internal_id=m.group("id"),
                category=(m.group("category") or "").strip(),
                title=m.group("title").strip(),
                severity=current_severity,
                fields=fields,
                raw_block=raw_block,
            ))
            continue
        i += 1

    return findings


# --- ID mapping --------------------------------------------------------

ID_DIGITS_RE = re.compile(r"^[A-Z](\d+)$")


def map_id(audit_internal_id: str, prefix: str) -> str:
    """S001 → SEC-001. Pads to 3 digits if shorter."""
    m = ID_DIGITS_RE.match(audit_internal_id)
    if not m:
        raise ValueError(f"unrecognized audit-internal ID: {audit_internal_id!r}")
    n = int(m.group(1))
    return f"{prefix}-{n:03d}"


# --- WorkItem construction --------------------------------------------

def build_work_item(
    finding: ParsedFinding,
    *,
    work_item_id: str,
    project: str,
    workspace: str,
    audit_type: str,
    audit_ts: str,
    audit_dir: Path,
    project_dir: Path,
) -> WorkItem:
    """Map a parsed finding into a WorkItem dataclass."""
    f = finding.fields
    priority = SEVERITY_TO_PRIORITY.get(finding.severity, "none")
    labels = ["audit", f"audit:{audit_type}"]
    if finding.category:
        labels.append(f"category:{finding.category.lower().replace(' ', '-')}")

    description = _compose_description(finding)
    acceptance = _compose_acceptance(finding)
    source_ref = str(audit_dir.relative_to(project_dir)) + "/REPORT.md"

    wi = WorkItem(
        id=work_item_id,
        title=finding.title,
        project=project,
        workspace=workspace,
        state="backlog",
        priority=priority,
        labels=labels,
        source="audit",
        source_ref=source_ref,
        audit_id=finding.audit_internal_id,
        audit_type=audit_type,
        audit_severity=finding.severity,
        location_hint=f.get("location"),
        description=description,
        acceptance=acceptance,
    )
    wi.append_activity(
        f"Ingested from audit {audit_type} @ {audit_ts} "
        f"(internal id {finding.audit_internal_id}, severity {finding.severity})"
    )
    return wi


def _compose_description(f: ParsedFinding) -> str:
    """Use the Issue field as the primary description; fall back to the
    full raw block (minus the Task header line) if Issue is missing."""
    issue = f.fields.get("issue")
    if issue:
        out = [issue]
        # Light-touch context: include CWE/Apple + Platform + Verification if present
        ctx_bits = []
        for key in ("cwe/apple", "platform", "verification"):
            v = f.fields.get(key)
            if v:
                # Re-title-case the key for human display
                label = {"cwe/apple": "CWE/Apple", "platform": "Platform",
                         "verification": "Verification"}[key]
                ctx_bits.append(f"- **{label}:** {v}")
        if ctx_bits:
            out.append("")
            out.extend(ctx_bits)
        loc = f.fields.get("location")
        if loc:
            out.append(f"- **Location:** {loc}")
        return "\n".join(out)
    # Fall-through: include the raw block minus the leading header.
    body = re.sub(r"^\*\*Task:[^\n]*\*\*\s*\n?", "", f.raw_block, count=1)
    return body.strip()


def _compose_acceptance(f: ParsedFinding) -> str:
    """Combine Remediation + Verification step into acceptance criteria."""
    remediation = f.fields.get("remediation", "")
    verif_step = f.fields.get("verification step") or f.fields.get("verification steps")
    op_note = f.fields.get("operational note")
    parts = []
    if remediation:
        parts.append(f"**Remediation:** {remediation}")
    if verif_step:
        parts.append(f"**Verification step:** {verif_step}")
    if op_note:
        parts.append(f"**Operational note:** {op_note}")
    return "\n\n".join(parts)


# --- INGEST.md manifest -----------------------------------------------

def write_ingest_manifest(
    audit_dir: Path,
    *,
    audit_type: str,
    audit_ts: str,
    project: str,
    workspace: str,
    findings: list[ParsedFinding],
    work_item_paths: list[tuple[str, Path]],  # (id, path)
) -> Path:
    """Write the INGEST.md manifest. Lists what was created with severity tallies."""
    sev_counts: dict[str, int] = {}
    for f in findings:
        sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1

    lines = [
        f"# Ingest manifest — {audit_type} @ {audit_ts}",
        "",
        f"- Workspace: `{workspace}`",
        f"- Project: `{project}`",
        f"- Audit dir: `{audit_dir}`",
        f"- Ingested at: {now_iso()}",
        f"- Findings: {len(findings)}",
        "",
        "## Severity tally",
        "",
        "| Severity | Count |",
        "|---|---:|",
    ]
    for sev in ("critical", "high", "medium", "low", "informational"):
        n = sev_counts.get(sev, 0)
        if n:
            lines.append(f"| {sev} | {n} |")
    lines += [
        "",
        "## Work items created",
        "",
        "| ID | Audit ID | Severity | Title |",
        "|---|---|---|---|",
    ]
    for f, (wi_id, _) in zip(findings, work_item_paths):
        title = f.title.replace("|", "\\|")
        lines.append(f"| {wi_id} | {f.audit_internal_id} | {f.severity} | {title} |")
    lines += [
        "",
        "## Next step",
        "",
        "Promote these into the project work-items pool with "
        "`/plane-audit-promote`. Promotion matches existing work items "
        "by `(audit_type, audit_id)` and re-opens completed items or "
        "creates new ones as appropriate.",
        "",
    ]
    out = audit_dir / "INGEST.md"
    out.write_text("\n".join(lines))
    return out


# --- main --------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("audit_dir", type=Path,
                    help="Audit directory containing REPORT.md and MANIFEST.json.")
    args = ap.parse_args()

    audit_dir = args.audit_dir.resolve()
    report_path = audit_dir / "REPORT.md"
    manifest_path = audit_dir / "MANIFEST.json"

    for p in (report_path, manifest_path):
        if not p.exists():
            print(f"error: missing {p}", file=sys.stderr)
            return 1

    manifest = json.loads(manifest_path.read_text())
    audit_name = manifest["audit_name"]
    org_repo = manifest["org_repo"]
    org, repo = org_repo.split("/", 1)
    audit_ts = manifest["report_ts"]

    prefix = AUDIT_PREFIX.get(audit_name)
    if not prefix:
        print(f"error: no ID prefix mapping for audit_name={audit_name!r}", file=sys.stderr)
        print(f"       known: {sorted(AUDIT_PREFIX.keys())}", file=sys.stderr)
        return 2

    text = report_path.read_text()
    findings = parse_report(text)
    if not findings:
        # Not a fatal error — an audit with zero in-tier findings is fine.
        print(f"warning: parsed 0 findings from {report_path}", file=sys.stderr)

    # Build work items and write them.
    work_item_paths: list[tuple[str, Path]] = []
    project_dir = audit_dir.parent.parent  # <project>/audits/<TS>-<name>/  → <project>/
    for f in findings:
        wi_id = map_id(f.audit_internal_id, prefix)
        wi = build_work_item(
            f,
            work_item_id=wi_id,
            project=repo, workspace=org,
            audit_type=audit_name, audit_ts=audit_ts,
            audit_dir=audit_dir, project_dir=project_dir,
        )
        errs = wi.validate()
        if errs:
            print(f"error: invalid work item for {wi_id}: {errs}", file=sys.stderr)
            return 3
        out = audit_work_item_path(audit_dir, wi_id)
        wi.save(out)
        work_item_paths.append((wi_id, out))

    # INGEST.md manifest
    manifest_out = write_ingest_manifest(
        audit_dir,
        audit_type=audit_name, audit_ts=audit_ts,
        project=repo, workspace=org,
        findings=findings, work_item_paths=work_item_paths,
    )

    print(f"audit dir: {audit_dir}")
    print(f"audit:     {audit_name} ({prefix})")
    print(f"findings:  {len(findings)}")
    for f, (wi_id, p) in zip(findings, work_item_paths):
        print(f"  {wi_id:<10}  {f.severity:<14}  {f.title[:60]}")
    print(f"manifest:  {manifest_out}")
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
