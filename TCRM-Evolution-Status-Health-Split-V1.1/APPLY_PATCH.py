#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PATCH_NAME = "TCRM-Evolution-Status-Health-Split-V1.1"
MARKER = "TCRM_EVOLUTION_STATUS_DIAGNOSTICS_V1_1"

def fail(message: str) -> None:
    raise SystemExit(f"[{PATCH_NAME}] ERROR: {message}")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)

def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM").resolve()
    target = root / "server/services/waGatewayIntegrationService.ts"
    if not target.is_file():
        fail(f"missing target: {target}")

    text = target.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"[{PATCH_NAME}] already applied")
        return
    if "TCRM_EVOLUTION_STATUS_HEALTH_SPLIT_V1" not in text:
        fail("V1 health/status split marker is missing; apply V1 first")

    old_status = '''  const [local, remoteResult] = await Promise.all([\n    getLocalSessions(actor),\n    gatewayRequest("/instance/fetchInstances"),\n  ]);\n  // TCRM_EVOLUTION_STATUS_HEALTH_SPLIT_V1\n'''
    new_status = '''  // TCRM_EVOLUTION_STATUS_DIAGNOSTICS_V1_1\n  // gatewayRequest() performs gateway preflight before its internal try/catch.\n  // Keep getStatus resilient to DNS/allowlist/config preflight errors so the\n  // UI receives sanitized diagnostics instead of a rejected tRPC query.\n  const safeStatusRequest = async (path: string) => {\n    try {\n      return await gatewayRequest(path);\n    } catch (error: any) {\n      return {\n        success: false,\n        status:\n          error instanceof WAGatewayRequestError\n            ? Number(error.status || 0)\n            : 0,\n        error: sanitizeGatewayError(error?.message || error),\n        response: null,\n      };\n    }\n  };\n  const [local, remoteResult] = await Promise.all([\n    getLocalSessions(actor),\n    safeStatusRequest("/instance/fetchInstances"),\n  ]);\n  // TCRM_EVOLUTION_STATUS_HEALTH_SPLIT_V1\n'''
    text = replace_once(text, old_status, new_status, "status request guard")

    old_health = '''  const healthResult = remoteResult.success\n    ? { success: true, status: remoteResult.status, error: null, response: null }\n    : await gatewayRequest("/healthz");\n'''
    new_health = '''  const healthResult = remoteResult.success\n    ? { success: true, status: remoteResult.status, error: null, response: null }\n    : await safeStatusRequest("/healthz");\n'''
    text = replace_once(text, old_health, new_health, "health fallback guard")

    backup = target.with_name(target.name + ".evolution-status-health-split-v1.1.bak")
    if not backup.exists():
        shutil.copy2(target, backup)
    target.write_text(text, encoding="utf-8")

    print(f"[{PATCH_NAME}] applied")
    print(f"changed: {target.relative_to(root)}")
    print(f"backup:  {backup.relative_to(root)}")

if __name__ == "__main__":
    main()
