#!/usr/bin/env python3
from pathlib import Path
import sys

PATCH_ID = "TCRM_EVOLUTION_STATUS_HEALTH_SPLIT_V1"

def require(text: str, needle: str, label: str):
    if needle not in text:
        raise RuntimeError(f"VERIFY FAILED: {label}")

def forbid(text: str, needle: str, label: str):
    if needle in text:
        raise RuntimeError(f"VERIFY FAILED: {label}")

def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM").resolve()
    backend = root / "server/services/waGatewayIntegrationService.ts"
    frontend = root / "client/src/pages/wa/WAGatewayInbox.tsx"

    backend_text = backend.read_text(encoding="utf-8")
    frontend_text = frontend.read_text(encoding="utf-8")

    require(backend_text, PATCH_ID, "backend marker missing")
    require(backend_text, 'await gatewayRequest("/healthz")', "health fallback missing")
    require(backend_text, 'gatewayState', "gateway state missing")
    require(backend_text, 'statusEndpointAvailable: Boolean(remoteResult.success)', "status endpoint flag missing")
    require(backend_text, 'healthHttpStatus: healthHttpStatus || null', "health HTTP status missing")
    require(backend_text, 'success: remoteResult.success', "legacy success semantics were not preserved")

    require(frontend_text, PATCH_ID, "frontend marker missing")
    require(frontend_text, 'degraded: "Evolution online · status unavailable"', "English degraded copy missing")
    require(frontend_text, 'degraded: "Evolution متاح · حالة الحسابات غير متاحة"', "Arabic degraded copy missing")
    require(frontend_text, 'const gatewayOnline = gatewayState !== "offline";', "frontend state split missing")
    require(frontend_text, 'gatewayState === "degraded"', "degraded badge state missing")
    require(frontend_text, 'gatewayBadgeTitle', "admin diagnostic title missing")
    forbid(frontend_text, 'const gatewayOnline = Boolean((statusQ.data as any)?.success);', "old misleading badge logic still present")

    print(f"{PATCH_ID}: verification passed")
    print("Expected UI states: online / degraded / offline")
    print("Legacy getStatus.success remains tied to fetchInstances for compatibility.")
    print("No DB/schema/permission/send-path verification changes are required.")

if __name__ == "__main__":
    main()
