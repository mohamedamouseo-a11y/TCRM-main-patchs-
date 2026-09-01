#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys

PATCH_ID = "TCRM_EVOLUTION_STATUS_HEALTH_SPLIT_V1"

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)

def backup(path: Path):
    target = path.with_name(path.name + ".evolution-status-health-split-v1.bak")
    if not target.exists():
        shutil.copy2(path, target)

def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM").resolve()
    backend = root / "server/services/waGatewayIntegrationService.ts"
    frontend = root / "client/src/pages/wa/WAGatewayInbox.tsx"

    for path in (backend, frontend):
        if not path.exists():
            raise FileNotFoundError(f"Required TCRM file not found: {path}")

    backend_text = backend.read_text(encoding="utf-8")
    if PATCH_ID not in backend_text:
        backend_text = replace_once(
            backend_text,
            '''  const [local, remoteResult] = await Promise.all([\n    getLocalSessions(actor),\n    gatewayRequest("/instance/fetchInstances"),\n  ]);\n  const remote = remoteInstances(remoteResult.response);\n''',
            '''  const [local, remoteResult] = await Promise.all([\n    getLocalSessions(actor),\n    gatewayRequest("/instance/fetchInstances"),\n  ]);\n  // TCRM_EVOLUTION_STATUS_HEALTH_SPLIT_V1\n  // Keep the existing status endpoint as the authoritative account-state call.\n  // Only fall back to /healthz when that call fails, so healthy installations\n  // do not pay for an extra Evolution request every 15 seconds.\n  const healthResult = remoteResult.success\n    ? { success: true, status: remoteResult.status, error: null, response: null }\n    : await gatewayRequest("/healthz");\n  const remote = remoteInstances(remoteResult.response);\n''',
            "backend health fallback",
        )
        backend_text = replace_once(
            backend_text,
            '''      success: false,\n      connected: false,\n      status: "not_configured",\n      account: null,\n''',
            '''      success: false,\n      connected: false,\n      gatewayOnline: false,\n      gatewayState: "offline" as const,\n      healthEndpointAvailable: false,\n      statusEndpointAvailable: false,\n      healthHttpStatus: null,\n      statusHttpStatus: null,\n      healthError: "Evolution API is not fully configured",\n      statusError: "Evolution API is not fully configured",\n      status: "not_configured",\n      account: null,\n''',
            "backend not-configured state",
        )
        backend_text = replace_once(
            backend_text,
            '''  if (remoteResult.success) await recordGatewayError(null);\n  else await recordGatewayError(remoteResult.error);\n\n  return {\n    success: remoteResult.success,\n    connected: connectedAccounts > 0,\n''',
            '''  if (remoteResult.success) await recordGatewayError(null);\n  else await recordGatewayError(remoteResult.error);\n\n  const healthHttpStatus = Number(healthResult.status || 0);\n  const statusHttpStatus = Number(remoteResult.status || 0);\n  // An HTTP response (even 401/404/5xx) proves the Evolution service is reachable.\n  // "Offline" is reserved for transport/DNS/TLS/timeout failures where neither\n  // the status endpoint nor /healthz returned an HTTP response.\n  const gatewayReachable = healthHttpStatus > 0 || statusHttpStatus > 0;\n  const gatewayOnline = Boolean(\n    remoteResult.success || healthResult.success || gatewayReachable\n  );\n  const gatewayState = remoteResult.success\n    ? ("online" as const)\n    : gatewayOnline\n      ? ("degraded" as const)\n      : ("offline" as const);\n\n  return {\n    success: remoteResult.success,\n    connected: connectedAccounts > 0,\n    gatewayOnline,\n    gatewayState,\n    healthEndpointAvailable: Boolean(healthResult.success),\n    statusEndpointAvailable: Boolean(remoteResult.success),\n    healthHttpStatus: healthHttpStatus || null,\n    statusHttpStatus: statusHttpStatus || null,\n    healthError: healthResult.error || null,\n    statusError: remoteResult.error || null,\n''',
            "backend status classification",
        )
        backup(backend)
        backend.write_text(backend_text, encoding="utf-8")

    frontend_text = frontend.read_text(encoding="utf-8")
    if PATCH_ID not in frontend_text:
        frontend_text = replace_once(
            frontend_text,
            '''const text: Record<"ar" | "en", WhatsAppInboxCopy & { title: string; subtitle: string; online: string; offline: string }> = {''',
            '''const text: Record<"ar" | "en", WhatsAppInboxCopy & { title: string; subtitle: string; online: string; degraded: string; offline: string }> = {''',
            "frontend copy type",
        )
        frontend_text = replace_once(
            frontend_text,
            '''    title: "محادثات واتساب", subtitle: "صندوق وارد موحّد لكل أرقام واتساب المسموح لك بها.", online: "Evolution متاح", offline: "Evolution غير متاح",''',
            '''    title: "محادثات واتساب", subtitle: "صندوق وارد موحّد لكل أرقام واتساب المسموح لك بها.", online: "Evolution متاح", degraded: "Evolution متاح · حالة الحسابات غير متاحة", offline: "Evolution غير متاح",''',
            "frontend Arabic copy",
        )
        frontend_text = replace_once(
            frontend_text,
            '''    title: "WhatsApp Inbox", subtitle: "One focused inbox for every WhatsApp account you can access.", online: "Evolution online", offline: "Evolution offline",''',
            '''    title: "WhatsApp Inbox", subtitle: "One focused inbox for every WhatsApp account you can access.", online: "Evolution online", degraded: "Evolution online · status unavailable", offline: "Evolution offline",''',
            "frontend English copy",
        )
        frontend_text = replace_once(
            frontend_text,
            '''  const gatewayOnline = Boolean((statusQ.data as any)?.success);\n  const contextVisible = isLargeDesktop ? desktopContextVisible : contextOpen;\n''',
            '''  // TCRM_EVOLUTION_STATUS_HEALTH_SPLIT_V1\n  const gatewayStatus = statusQ.data as any;\n  const gatewayState = String(\n    gatewayStatus?.gatewayState ||\n      (gatewayStatus?.gatewayOnline === true || gatewayStatus?.success === true\n        ? "online"\n        : "offline")\n  );\n  const gatewayOnline = gatewayState !== "offline";\n  const gatewayDegraded = gatewayState === "degraded";\n  const gatewayBadgeLabel = gatewayDegraded\n    ? c.degraded\n    : gatewayOnline\n      ? c.online\n      : c.offline;\n  const gatewayAdminStatusCode = isAdmin\n    ? Number(\n        gatewayStatus?.statusHttpStatus ||\n          gatewayStatus?.healthHttpStatus ||\n          0\n      )\n    : 0;\n  const gatewayAdminDetail = isAdmin\n    ? String(\n        gatewayStatus?.statusError ||\n          gatewayStatus?.healthError ||\n          ""\n      ).trim()\n    : "";\n  const gatewayBadgeTitle =\n    isAdmin && (gatewayAdminStatusCode || gatewayAdminDetail)\n      ? [\n          gatewayAdminStatusCode ? `HTTP ${gatewayAdminStatusCode}` : "",\n          gatewayAdminDetail,\n        ]\n          .filter(Boolean)\n          .join(" · ")\n      : undefined;\n  const contextVisible = isLargeDesktop ? desktopContextVisible : contextOpen;\n''',
            "frontend gateway state",
        )
        frontend_text = replace_once(
            frontend_text,
            '''            <div><div className="flex items-center gap-2"><p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">Evolution API</p><span className={cn("h-2 w-2 rounded-full", gatewayOnline ? "bg-emerald-500" : "bg-amber-500")} /></div><h1 className="mt-0.5 text-xl font-bold tracking-tight text-slate-950 dark:text-white sm:text-2xl">{c.title}</h1><p className="mt-0.5 text-xs text-slate-500 sm:text-sm">{c.subtitle}</p></div>\n            <div className="flex items-center gap-2"><Badge className={gatewayOnline ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}>{gatewayOnline ? c.online : c.offline}</Badge><Button variant="outline" size="sm" disabled={statusQ.isFetching || chatsQ.isFetching} onClick={refreshAll}><RefreshCw className={cn("h-4 w-4", (statusQ.isFetching || chatsQ.isFetching) && "animate-spin")} />{statusQ.isFetching || chatsQ.isFetching ? c.refreshing : c.refresh}</Button>{selected && isLargeDesktop && desktopContextVisible && <Button variant="ghost" size="icon" onClick={() => setDesktopContextVisible(false)} aria-label={c.closePanel}><PanelRightClose className="h-4 w-4" /></Button>}</div>\n''',
            '''            <div><div className="flex items-center gap-2"><p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">Evolution API</p><span className={cn("h-2 w-2 rounded-full", gatewayState === "online" ? "bg-emerald-500" : gatewayState === "degraded" ? "bg-amber-500" : "bg-red-500")} /></div><h1 className="mt-0.5 text-xl font-bold tracking-tight text-slate-950 dark:text-white sm:text-2xl">{c.title}</h1><p className="mt-0.5 text-xs text-slate-500 sm:text-sm">{c.subtitle}</p></div>\n            <div className="flex items-center gap-2">\n              <Badge\n                title={gatewayBadgeTitle}\n                className={gatewayState === "online" ? "bg-emerald-100 text-emerald-700" : gatewayState === "degraded" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}\n              >\n                {gatewayBadgeLabel}\n              </Badge>\n              {isAdmin && gatewayState !== "online" && (gatewayAdminStatusCode || gatewayAdminDetail) && (\n                <span className="hidden max-w-[240px] truncate text-[11px] text-slate-500 xl:inline" title={gatewayBadgeTitle}>\n                  {gatewayAdminStatusCode ? `HTTP ${gatewayAdminStatusCode}` : gatewayAdminDetail}\n                </span>\n              )}\n              <Button variant="outline" size="sm" disabled={statusQ.isFetching || chatsQ.isFetching} onClick={refreshAll}><RefreshCw className={cn("h-4 w-4", (statusQ.isFetching || chatsQ.isFetching) && "animate-spin")} />{statusQ.isFetching || chatsQ.isFetching ? c.refreshing : c.refresh}</Button>{selected && isLargeDesktop && desktopContextVisible && <Button variant="ghost" size="icon" onClick={() => setDesktopContextVisible(false)} aria-label={c.closePanel}><PanelRightClose className="h-4 w-4" /></Button>}\n            </div>\n''',
            "frontend badge",
        )
        backup(frontend)
        frontend.write_text(frontend_text, encoding="utf-8")

    print(f"{PATCH_ID}: applied successfully")
    print(f"Backend: {backend}")
    print(f"Frontend: {frontend}")
    print("No DB/schema/permissions/message-send changes were made.")

if __name__ == "__main__":
    main()
