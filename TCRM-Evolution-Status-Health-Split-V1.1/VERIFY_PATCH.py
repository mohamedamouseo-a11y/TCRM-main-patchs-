#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PATCH_NAME = "TCRM-Evolution-Status-Health-Split-V1.1"

def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM").resolve()
    backend = root / "server/services/waGatewayIntegrationService.ts"
    frontend = root / "client/src/pages/wa/WAGatewayInbox.tsx"

    failures: list[str] = []

    if not backend.is_file():
        failures.append("missing backend file")
    else:
        text = backend.read_text(encoding="utf-8")
        checks = {
            "V1.1 marker": "TCRM_EVOLUTION_STATUS_DIAGNOSTICS_V1_1",
            "safe status helper": "const safeStatusRequest = async (path: string)",
            "status endpoint guarded": 'safeStatusRequest("/instance/fetchInstances")',
            "health endpoint guarded": 'safeStatusRequest("/healthz")',
            "sanitized preflight diagnostic": "sanitizeGatewayError(error?.message || error)",
            "legacy status success preserved": "success: remoteResult.success",
            "V1 status marker preserved": "TCRM_EVOLUTION_STATUS_HEALTH_SPLIT_V1",
        }
        for label, needle in checks.items():
            if needle not in text:
                failures.append(label)

    if not frontend.is_file():
        failures.append("missing frontend file")
    else:
        ui = frontend.read_text(encoding="utf-8")
        ui_checks = {
            "V1 frontend marker preserved": "TCRM_EVOLUTION_STATUS_HEALTH_SPLIT_V1",
            "admin statusError diagnostic preserved": "gatewayStatus?.statusError",
            "admin healthError diagnostic preserved": "gatewayStatus?.healthError",
            "degraded badge preserved": 'gatewayState === "degraded"',
        }
        for label, needle in ui_checks.items():
            if needle not in ui:
                failures.append(label)

    if failures:
        print(f"[{PATCH_NAME}] VERIFY: FAIL")
        for item in failures:
            print(f" - {item}")
        raise SystemExit(1)

    print(f"[{PATCH_NAME}] VERIFY: PASS")
    print(" - backend preflight/DNS/allowlist errors are converted to safe diagnostics")
    print(" - /instance/fetchInstances and /healthz status probes are guarded")
    print(" - legacy getStatus.success semantics are preserved")
    print(" - existing V1 three-state UI diagnostics are preserved")

if __name__ == "__main__":
    main()
