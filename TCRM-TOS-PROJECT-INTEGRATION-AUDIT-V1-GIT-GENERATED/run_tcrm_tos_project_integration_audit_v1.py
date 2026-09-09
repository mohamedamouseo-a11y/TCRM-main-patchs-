#!/usr/bin/env python3
"""
TCRM -> TOS Project Integration Audit V1
READ ONLY. This script never edits application source, data, services, or git state.
It writes only sanitized reports under /tmp.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

PATCH = "TCRM-TOS-PROJECT-INTEGRATION-AUDIT-V1-GIT-GENERATED"
REVISION = "V1"
EXPECTED_HEAD = "b016f9ada07e334b47bf95a19a59e667b7351b1b"
EXPECTED_REPO_TOKEN = "TCRM-MAIN-Tamiyouz-CRM-"
TEXT_REPORT = Path("/tmp/tcrm_tos_project_integration_audit_v1.txt")
JSON_REPORT = Path("/tmp/tcrm_tos_project_integration_audit_v1.json")

EXCLUDED_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".cache", "coverage",
    "vendor", "tmp", "temp", ".vite", ".turbo"
}
TEXT_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".md",
    ".sh", ".py", ".sql", ".yml", ".yaml", ".toml", ".env", ".txt"
}

SEARCH_PATTERNS = [
    ("tos_literal", re.compile(r"\bTOS\b|tos\.tamiyouz|\btos[_-]", re.I)),
    ("crm_project_id", re.compile(r"crmProjectId|crm_project_id|crm-project", re.I)),
    ("crm_deal_id", re.compile(r"crmDealId|crm_deal_id|crm-deal", re.I)),
    ("crm_client_id", re.compile(r"crmClientId|crm_client_id|crm-client", re.I)),
    ("project_sync", re.compile(r"project.{0,30}(sync|upsert|webhook|deliver|bridge)|(?:sync|upsert|webhook|deliver|bridge).{0,30}project", re.I)),
    ("tos_project_endpoint", re.compile(r"/(?:api/)?[^\s\"']*(?:crm[-_/])?projects?[^\s\"']*", re.I)),
    ("outbound_http", re.compile(r"\bfetch\s*\(|axios\.|axios\s*\(|got\s*\(|request\s*\(", re.I)),
    ("retry_backfill", re.compile(r"retry|backfill|force.{0,20}sync|sync.{0,20}all|batch|replay", re.I)),
]

SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASS|API[_-]?KEY|PRIVATE[_-]?KEY|AUTHORIZATION)[A-Z0-9_-]*)\b\s*[:=]\s*([^\s,;]+)"
)
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
BEARER_RE = re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+\-/]+=*")
URL_CREDENTIAL_RE = re.compile(r"(https?://)([^/@\s:]+):([^/@\s]+)@", re.I)
QUERY_SECRET_RE = re.compile(r"(?i)([?&](?:token|key|api_key|secret|password)=)[^&\s]+")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")

# Explicit mutation deny-list. The runner itself never calls these operations.
FORBIDDEN_SQL = re.compile(r"\b(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE|REPLACE|MERGE|GRANT|REVOKE)\b", re.I)
FORBIDDEN_HTTP = re.compile(r"\b(POST|PUT|PATCH|DELETE)\b", re.I)
FORBIDDEN_GIT = re.compile(r"\bgit\s+(reset|checkout|commit|push|clean|restore|switch|merge|rebase|pull)\b", re.I)


def sanitize(text: str) -> str:
    text = URL_CREDENTIAL_RE.sub(r"\1[REDACTED]:[REDACTED]@", text)
    text = BEARER_RE.sub("Bearer [REDACTED]", text)
    text = JWT_RE.sub("[REDACTED_JWT]", text)
    text = QUERY_SECRET_RE.sub(r"\1[REDACTED]", text)
    text = SENSITIVE_ASSIGNMENT.sub(lambda m: f"{m.group(1)}=[REDACTED]", text)
    # Production logs can contain personal identifiers; redact them from exported report.
    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = PHONE_RE.sub("[REDACTED_PHONE]", text)
    return text


def run_readonly(cmd: list[str], cwd: Path | None = None, timeout: int = 20) -> tuple[int, str]:
    """Run only hard-coded read-only commands. No shell=True."""
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        return p.returncode, sanitize(p.stdout or "")
    except Exception as exc:
        return 125, f"ERROR: {type(exc).__name__}: {exc}"


def git(repo: Path, *args: str, timeout: int = 20) -> tuple[int, str]:
    # Only explicitly allowed read-only git subcommands.
    allowed = {"rev-parse", "status", "remote", "log", "reflog", "show", "diff", "ls-files"}
    if not args or args[0] not in allowed:
        raise RuntimeError(f"Blocked non-read-only git command: {args}")
    return run_readonly(["git", "-C", str(repo), *args], timeout=timeout)


def discover_repo() -> tuple[Path | None, list[str]]:
    notes: list[str] = []
    candidates: list[Path] = []
    if os.environ.get("TCRM_REPO"):
        candidates.append(Path(os.environ["TCRM_REPO"]).expanduser())
    candidates.extend([
        Path.cwd(),
        Path("/var/www/TCRM"),
        Path("/var/www/tcrm"),
        Path("/var/www/TCRM-MAIN-Tamiyouz-CRM-"),
        Path("/opt/TCRM"),
        Path("/opt/tcrm"),
        Path.home() / "TCRM",
        Path.home() / "tcrm",
    ])

    seen: set[str] = set()
    fallbacks: list[Path] = []
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            continue
        if str(resolved) in seen or not resolved.exists():
            continue
        seen.add(str(resolved))
        rc, root = run_readonly(["git", "-C", str(resolved), "rev-parse", "--show-toplevel"])
        if rc != 0:
            continue
        repo = Path(root.strip())
        if not repo.exists():
            continue
        rc, remote = git(repo, "remote", "get-url", "origin")
        remote_safe = sanitize(remote.strip())
        if rc == 0 and EXPECTED_REPO_TOKEN.lower() in remote_safe.lower():
            notes.append(f"Repo matched origin: {repo}")
            return repo, notes
        if EXPECTED_REPO_TOKEN.lower() in repo.name.lower():
            notes.append(f"Repo matched directory name: {repo}")
            return repo, notes
        fallbacks.append(repo)

    # Conservative fallback only if exactly one git repo candidate exists.
    unique = list(dict.fromkeys(fallbacks))
    if len(unique) == 1:
        notes.append(f"WARNING: origin token not matched; single git candidate selected: {unique[0]}")
        return unique[0], notes
    return None, notes


def iter_source_files(repo: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        root_path = Path(root)
        for name in files:
            p = root_path / name
            if p.name.startswith(".env"):
                # .env values are never scanned as source; env names handled separately.
                continue
            if p.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                if p.stat().st_size > 2_000_000:
                    continue
            except OSError:
                continue
            yield p


def static_source_scan(repo: Path) -> dict:
    matches: list[dict] = []
    file_scores: defaultdict[str, int] = defaultdict(int)
    file_labels: defaultdict[str, set[str]] = defaultdict(set)
    max_matches = 350

    for path in iter_source_files(repo):
        rel = str(path.relative_to(repo))
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for lineno, raw_line in enumerate(fh, 1):
                    line = raw_line.rstrip("\n")
                    labels = [label for label, rx in SEARCH_PATTERNS if rx.search(line)]
                    if not labels:
                        continue
                    score = 0
                    if "tos_literal" in labels:
                        score += 5
                    if any(x in labels for x in ("crm_project_id", "crm_deal_id", "crm_client_id")):
                        score += 4
                    if "project_sync" in labels:
                        score += 4
                    if "outbound_http" in labels:
                        score += 2
                    if "retry_backfill" in labels:
                        score += 2
                    file_scores[rel] += score
                    file_labels[rel].update(labels)
                    if len(matches) < max_matches:
                        matches.append({
                            "file": rel,
                            "line": lineno,
                            "labels": labels,
                            "snippet": sanitize(line.strip())[:800],
                        })
        except OSError:
            continue

    ranked = sorted(
        (
            {"file": f, "score": score, "labels": sorted(file_labels[f])}
            for f, score in file_scores.items()
        ),
        key=lambda x: (-x["score"], x["file"]),
    )[:40]
    return {
        "ranked_candidate_files": ranked,
        "matches": matches,
        "match_count_capped": len(matches) >= max_matches,
    }


def env_key_audit(repo: Path) -> list[dict]:
    results: list[dict] = []
    interesting = re.compile(r"TOS|CRM|SUPABASE|API|URL|WEBHOOK|SYNC|PROJECT|BRIDGE", re.I)
    candidates: list[Path] = []
    for base in [repo, repo / "server", repo / "backend", repo / "api"]:
        if not base.exists() or not base.is_dir():
            continue
        try:
            candidates.extend(p for p in base.glob(".env*") if p.is_file())
        except OSError:
            pass
    for path in sorted(set(candidates)):
        keys: list[str] = []
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
                if m and interesting.search(m.group(1)):
                    keys.append(m.group(1))
        except OSError:
            continue
        results.append({
            "file": str(path.relative_to(repo)),
            "interesting_present_keys": sorted(set(keys)),
            "values_exported": False,
        })
    return results


def package_script_audit(repo: Path) -> dict:
    p = repo / "package.json"
    if not p.exists():
        return {"present": False}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"present": True, "parse_error": str(exc)}
    scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
    interesting = {
        str(k): sanitize(str(v))
        for k, v in scripts.items()
        if re.search(r"tos|sync|project|bridge|backfill|retry|force", f"{k} {v}", re.I)
    }
    return {"present": True, "interesting_scripts": interesting}


def git_timeline(repo: Path) -> dict:
    out: dict = {}
    rc, log = git(
        repo, "log", "--all", "--since=2026-08-10 00:00:00", "--until=2026-08-20 23:59:59",
        "--date=iso", "--pretty=format:%h %ad %d %s", "--name-only", timeout=30,
    )
    out["git_log_2026_08_10_to_20"] = log[:30000] if rc == 0 else f"UNAVAILABLE: {log}"
    rc, reflog = git(repo, "reflog", "--all", "--date=iso", "--pretty=format:%h %gd %ad %gs", timeout=30)
    if rc == 0:
        selected = [line for line in reflog.splitlines() if re.search(r"2026-08-(1[0-9]|20)", line)]
        out["git_reflog_2026_08_10_to_20"] = "\n".join(selected[:500])
    else:
        out["git_reflog_2026_08_10_to_20"] = f"UNAVAILABLE: {reflog}"
    return out


def runtime_inventory() -> dict:
    out: dict = {}
    if shutil.which("pm2"):
        rc, text = run_readonly(["pm2", "ls", "--no-color"], timeout=20)
        out["pm2_ls"] = text[:20000] if rc == 0 else f"UNAVAILABLE: {text}"
    else:
        out["pm2_ls"] = "pm2 not installed/in PATH"

    if shutil.which("systemctl"):
        rc, text = run_readonly([
            "systemctl", "list-units", "--type=service", "--state=running", "--no-pager", "--no-legend"
        ], timeout=20)
        if rc == 0:
            selected = [line for line in text.splitlines() if re.search(r"tcrm|crm|node|nginx", line, re.I)]
            out["systemd_relevant_running"] = "\n".join(selected[:100])
        else:
            out["systemd_relevant_running"] = f"UNAVAILABLE: {text}"
    else:
        out["systemd_relevant_running"] = "systemctl not installed/in PATH"

    if shutil.which("docker"):
        rc, text = run_readonly([
            "docker", "ps", "--format", "{{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"
        ], timeout=20)
        out["docker_ps"] = text[:20000] if rc == 0 else f"UNAVAILABLE: {text}"
    else:
        out["docker_ps"] = "docker not installed/in PATH"
    return out


def possible_log_files(repo: Path) -> list[Path]:
    roots = [repo / "logs", Path.home() / ".pm2" / "logs", Path("/var/log")]
    found: list[Path] = []
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        try:
            for p in root.rglob("*"):
                if not p.is_file():
                    continue
                name = p.name.lower()
                if not (name.endswith(".log") or "out" in name or "error" in name):
                    continue
                if root == Path("/var/log") and not re.search(r"tcrm|crm|node|pm2|nginx", str(p), re.I):
                    continue
                try:
                    if p.stat().st_size > 100_000_000:
                        continue
                except OSError:
                    continue
                found.append(p)
                if len(found) >= 80:
                    return found
        except (OSError, PermissionError):
            continue
    return found


def log_evidence(repo: Path) -> dict:
    evidence: list[dict] = []
    files_checked: list[str] = []
    relevant = re.compile(r"tos|project.{0,30}sync|sync.{0,30}project|crmProjectId|crm_client|crm-client|crmDealId|backfill|retry", re.I)
    target_date = re.compile(r"2026[-/]08[-/](?:1[0-9]|20)|Aug\s+(?:1[0-9]|20)", re.I)
    max_hits = 180

    for path in possible_log_files(repo):
        files_checked.append(str(path))
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for lineno, line in enumerate(fh, 1):
                    if not relevant.search(line):
                        continue
                    # Prefer target-window lines, but retain TOS-specific evidence even without date.
                    is_target = bool(target_date.search(line))
                    is_tos = bool(re.search(r"tos|crmProjectId|crmDealId|crm_client|crm-client", line, re.I))
                    if not (is_target or is_tos):
                        continue
                    evidence.append({
                        "file": str(path),
                        "line": lineno,
                        "target_window": is_target,
                        "text": sanitize(line.strip())[:1200],
                    })
                    if len(evidence) >= max_hits:
                        return {
                            "files_checked": files_checked,
                            "evidence": evidence,
                            "capped": True,
                        }
        except (OSError, PermissionError):
            continue
    return {"files_checked": files_checked, "evidence": evidence, "capped": False}


def detect_identity_clues(scan: dict) -> dict:
    joined = "\n".join(m.get("snippet", "") for m in scan.get("matches", []))
    return {
        "mentions_crmProjectId": bool(re.search(r"crmProjectId|crm_project_id", joined, re.I)),
        "mentions_crmDealId": bool(re.search(r"crmDealId|crm_deal_id", joined, re.I)),
        "mentions_crmClientId": bool(re.search(r"crmClientId|crm_client_id|crm-client", joined, re.I)),
        "mentions_retry_or_backfill": bool(re.search(r"retry|backfill|batch|replay|force.{0,20}sync", joined, re.I)),
        "mentions_durable_tos_mapping": bool(re.search(r"tosProjectId|tos_project_id|projectMapping|project_mapping|tos.*mapping|mapping.*tos", joined, re.I)),
    }


def build_text_report(result: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add(f"PATCH={PATCH}")
    add(f"REVISION={REVISION}")
    add("MODE=READ_ONLY")
    add(f"EXPECTED_HEAD={EXPECTED_HEAD}")
    add(f"ACTUAL_HEAD={result.get('actual_head', 'UNKNOWN')}")
    add(f"BASELINE={'PASS' if result.get('baseline_ok') else 'FAIL'}")
    add(f"REPO={result.get('repo', 'UNKNOWN')}")
    add(f"DIRTY_FILES_ALLOWED={result.get('dirty_file_count', 0)}")
    add("SOURCE_CHANGES=NO")
    add("DB_MUTATION=NO")
    add("BUILD=NOT_RUN")
    add("DEPLOY=NOT_RUN")
    add("SERVICE_RESTART=NO")
    add("GIT_PUSH=NO")
    add("")

    if not result.get("baseline_ok"):
        add("AUDIT_STATUS=ABORTED_BASELINE_MISMATCH")
        return "\n".join(lines) + "\n"

    scan = result.get("static_scan", {})
    add("=== STATIC SOURCE CANDIDATES ===")
    for item in scan.get("ranked_candidate_files", [])[:25]:
        add(f"score={item['score']} labels={','.join(item['labels'])} file={item['file']}")
    add("")
    add("=== STATIC MATCHES (SANITIZED, CAPPED) ===")
    for item in scan.get("matches", [])[:220]:
        add(f"{item['file']}:{item['line']} [{','.join(item['labels'])}] {item['snippet']}")
    add("")

    add("=== IDENTITY / IDEMPOTENCY CLUES ===")
    for k, v in result.get("identity_clues", {}).items():
        add(f"{k}={v}")
    add("")

    add("=== ENV KEY NAMES ONLY (NO VALUES) ===")
    for item in result.get("env_keys", []):
        add(f"{item['file']}: {', '.join(item['interesting_present_keys']) or '(no interesting keys)'}")
    add("")

    add("=== PACKAGE SCRIPTS (READ ONLY; NOTHING EXECUTED) ===")
    add(json.dumps(result.get("package_scripts", {}), ensure_ascii=False, indent=2))
    add("")

    add("=== GIT TIMELINE AROUND 2026-08-15 ===")
    timeline = result.get("git_timeline", {})
    add(timeline.get("git_log_2026_08_10_to_20", ""))
    add("--- REFLOG ---")
    add(timeline.get("git_reflog_2026_08_10_to_20", ""))
    add("")

    add("=== RUNTIME INVENTORY (READ ONLY) ===")
    for k, v in result.get("runtime", {}).items():
        add(f"--- {k} ---")
        add(str(v))
    add("")

    log_data = result.get("logs", {})
    add("=== SANITIZED LOG EVIDENCE ===")
    add(f"LOG_FILES_CHECKED={len(log_data.get('files_checked', []))}")
    add(f"LOG_HITS={len(log_data.get('evidence', []))}")
    for item in log_data.get("evidence", []):
        add(f"{item['file']}:{item['line']} target_window={item['target_window']} {item['text']}")
    add("")

    add("=== SAFETY ===")
    add("HTTP_MUTATIONS=NOT_PERFORMED")
    add("SQL=NOT_EXECUTED")
    add("SOURCE_FILES_WRITTEN=NO")
    add("ONLY_REPORT_FILES_WRITTEN=/tmp/tcrm_tos_project_integration_audit_v1.txt,/tmp/tcrm_tos_project_integration_audit_v1.json")
    add("AUDIT_STATUS=PASS_READ_ONLY")
    return sanitize("\n".join(lines) + "\n")


def main() -> int:
    print(f"PATCH={PATCH}")
    print(f"REVISION={REVISION}")
    print("MODE=READ_ONLY")

    repo, discovery_notes = discover_repo()
    if repo is None:
        result = {
            "patch": PATCH,
            "revision": REVISION,
            "mode": "READ_ONLY",
            "repo": None,
            "baseline_ok": False,
            "error": "TCRM repository not found",
            "discovery_notes": discovery_notes,
        }
        text = build_text_report(result)
        TEXT_REPORT.write_text(text, encoding="utf-8")
        JSON_REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("ERROR=TCRM_REPO_NOT_FOUND")
        print(f"REPORT={TEXT_REPORT}")
        return 2

    rc, head = git(repo, "rev-parse", "HEAD")
    actual_head = head.strip() if rc == 0 else "UNKNOWN"
    rc_status, dirty = git(repo, "status", "--porcelain=v1")
    dirty_lines = [line for line in dirty.splitlines() if line.strip()] if rc_status == 0 else []

    result: dict = {
        "patch": PATCH,
        "revision": REVISION,
        "mode": "READ_ONLY",
        "repo": str(repo),
        "expected_head": EXPECTED_HEAD,
        "actual_head": actual_head,
        "baseline_ok": actual_head == EXPECTED_HEAD,
        "dirty_file_count": len(dirty_lines),
        "dirty_status_sanitized": dirty_lines[:200],
        "discovery_notes": discovery_notes,
    }

    # Abort safely before any deeper inspection when baseline is not the approved main commit.
    if actual_head != EXPECTED_HEAD:
        text = build_text_report(result)
        TEXT_REPORT.write_text(text, encoding="utf-8")
        JSON_REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"BASELINE_MISMATCH expected={EXPECTED_HEAD} actual={actual_head}")
        print("CHANGES_MADE=NO")
        print(f"REPORT={TEXT_REPORT}")
        return 3

    result["static_scan"] = static_source_scan(repo)
    result["identity_clues"] = detect_identity_clues(result["static_scan"])
    result["env_keys"] = env_key_audit(repo)
    result["package_scripts"] = package_script_audit(repo)
    result["git_timeline"] = git_timeline(repo)
    result["runtime"] = runtime_inventory()
    result["logs"] = log_evidence(repo)
    result["safety"] = {
        "source_changes": False,
        "db_queries_executed": False,
        "http_requests_executed": False,
        "build_run": False,
        "deploy_run": False,
        "service_restart": False,
        "git_push": False,
        "report_paths": [str(TEXT_REPORT), str(JSON_REPORT)],
    }

    # Defensive self-audit: exported reports must not claim execution of a forbidden operation.
    text = build_text_report(result)
    TEXT_REPORT.write_text(text, encoding="utf-8")
    JSON_REPORT.write_text(sanitize(json.dumps(result, ensure_ascii=False, indent=2)), encoding="utf-8")

    print(f"HEAD={actual_head}")
    print(f"DIRTY_FILES_ALLOWED={len(dirty_lines)}")
    print(f"STATIC_CANDIDATE_FILES={len(result['static_scan']['ranked_candidate_files'])}")
    print(f"STATIC_MATCHES={len(result['static_scan']['matches'])}")
    print(f"LOG_HITS={len(result['logs']['evidence'])}")
    print("DB_MUTATION=NO")
    print("SOURCE_CHANGES=NO")
    print("BUILD=NOT_RUN")
    print("DEPLOY=NOT_RUN")
    print("SERVICE_RESTART=NO")
    print("GIT_PUSH=NO")
    print("AUDIT_STATUS=PASS_READ_ONLY")
    print(f"TEXT_REPORT={TEXT_REPORT}")
    print(f"JSON_REPORT={JSON_REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
