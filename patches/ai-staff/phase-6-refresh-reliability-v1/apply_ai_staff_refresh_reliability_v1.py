#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path.cwd()

FILES = {
    "darwish": (pathlib.Path("client/src/pages/DarwishPage.tsx"), "02214a9bdb3db6771edb0832737d996ef2ad21ec"),
    "zaghloul": (pathlib.Path("client/src/pages/ZaghloulV5Page.tsx"), "1cf4947be082609706008da5c8d4112f89f2829c"),
    "tara": (pathlib.Path("client/src/pages/TaraAgentPage.tsx"), "20f124868c997f17079c39ec97de655efe799ec2"),
    "felfel": (pathlib.Path("client/src/pages/FelfelPage.tsx"), "bc7fc40786d3c37944e5a51ebd33e0c6399cfddd"),
}


def git_blob(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def read(path: pathlib.Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: pathlib.Path, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def require_base() -> None:
    failures = []
    for name, (path, expected) in FILES.items():
        actual = git_blob(path)
        if actual != expected:
            failures.append(f"{name}: {path} expected {expected}, got {actual}")
    if failures:
        raise RuntimeError("Base blob mismatch:\n" + "\n".join(failures))


def patch_darwish(text: str) -> str:
    text = replace_once(
        text,
        '  const [clientId, setClientId] = useState<number | null>(null);\n',
        '''  const [clientId, setClientId] = useState<number | null>(null);
  const [manualRefreshPending, setManualRefreshPending] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);
''',
        "darwish refresh state",
    )
    text = replace_once(
        text,
        '''  const clientsQ = trpc.darwish.clients.useQuery({ search: clientSearch }, { enabled: clientSearch.trim().length > 1 });
  const refreshActionData = () => { void utils.darwish.actionStats.invalidate(); void utils.darwish.actions.invalidate(); };
''',
        '''  const clientsQ = trpc.darwish.clients.useQuery({ search: clientSearch }, { enabled: clientSearch.trim().length > 1 });

  const refreshDarwishData = async () => {
    if (manualRefreshPending) return;
    setManualRefreshPending(true);
    try {
      await utils.darwish.invalidate();
      const results = await Promise.all([
        healthQ.refetch(),
        linksQ.refetch(),
        jobsQ.refetch(),
        mappingCountsQ.refetch(),
        intelligenceStatsQ.refetch(),
        intelligenceQ.refetch(),
        supervisorQ.refetch(),
        alertsQ.refetch(),
        accountManagersQ.refetch(),
        digestQ.refetch(),
        actionStatsQ.refetch(),
        actionsQ.refetch(),
        actionCapabilitiesQ.refetch(),
      ]);
      const failed = results.find((result: any) => result?.error);
      if (failed?.error) throw failed.error;
      setLastRefreshedAt(new Date());
      toast.success(ar ? "تم تحديث بيانات درويش" : "Darwish data refreshed");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : (ar ? "تعذر تحديث بيانات درويش" : "Unable to refresh Darwish data"));
    } finally {
      setManualRefreshPending(false);
    }
  };

  const refreshActionData = () => { void utils.darwish.actionStats.invalidate(); void utils.darwish.actions.invalidate(); };
''',
        "darwish manual refresh handler",
    )
    text = replace_once(
        text,
        '''            <Button variant="outline" className="h-10 rounded-xl bg-background/70 font-bold" onClick={() => { void healthQ.refetch(); void linksQ.refetch(); void jobsQ.refetch(); void mappingCountsQ.refetch(); void intelligenceStatsQ.refetch(); void intelligenceQ.refetch(); void supervisorQ.refetch(); void alertsQ.refetch(); void accountManagersQ.refetch(); void digestQ.refetch(); void actionStatsQ.refetch(); void actionsQ.refetch(); void actionCapabilitiesQ.refetch(); }}><RefreshCw className="me-2 h-4 w-4" />{ar ? "تحديث البيانات" : "Refresh data"}</Button>
''',
        '''            <Button data-ai-staff-refresh="darwish-v1" variant="outline" className="h-10 rounded-xl bg-background/70 font-bold" disabled={manualRefreshPending} onClick={refreshDarwishData}><RefreshCw className={"me-2 h-4 w-4 " + (manualRefreshPending ? "animate-spin" : "")} />{manualRefreshPending ? (ar ? "جار التحديث..." : "Refreshing...") : (ar ? "تحديث البيانات" : "Refresh data")}</Button>
            {lastRefreshedAt ? <p className="text-[11px] font-medium text-muted-foreground">{ar ? "آخر تحديث" : "Last updated"}: {lastRefreshedAt.toLocaleTimeString(ar ? "ar-EG" : "en-US", { hour: "2-digit", minute: "2-digit" })}</p> : null}
''',
        "darwish refresh button",
    )
    return text


def patch_zaghloul(text: str) -> str:
    text = replace_once(
        text,
        '''// @ts-nocheck
import CRMLayout from "@/components/CRMLayout";
''',
        '''// @ts-nocheck
import { useState } from "react";
import CRMLayout from "@/components/CRMLayout";
''',
        "zaghloul useState import",
    )
    text = replace_once(
        text,
        '''import { trpc } from "@/lib/trpc";
import zaghloulAvatar from "@/assets/ai-staff/zaghloul-avatar-v2.jpg";
''',
        '''import { trpc } from "@/lib/trpc";
import { toast } from "sonner";
import zaghloulAvatar from "@/assets/ai-staff/zaghloul-avatar-v2.jpg";
''',
        "zaghloul toast import",
    )
    text = replace_once(
        text,
        '''  const { lang, isRTL } = useLanguage();
  const ar = lang === "ar";

  const healthQ = trpc.zaghloul.zaghloulV5.health.useQuery();
''',
        '''  const { lang, isRTL } = useLanguage();
  const ar = lang === "ar";
  const [manualRefreshPending, setManualRefreshPending] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);

  const healthQ = trpc.zaghloul.zaghloulV5.health.useQuery();
''',
        "zaghloul refresh state",
    )
    text = replace_once(
        text,
        '''  const webhooksQ = trpc.zaghloul.zaghloulV5.developer.webhooks.list.useQuery();
  const mcpQ = trpc.zaghloul.zaghloulV5.developer.mcp.status.useQuery();

  const healthy = healthQ.data?.status === "healthy";
''',
        '''  const webhooksQ = trpc.zaghloul.zaghloulV5.developer.webhooks.list.useQuery();
  const mcpQ = trpc.zaghloul.zaghloulV5.developer.mcp.status.useQuery();

  const refreshZaghloulData = async () => {
    if (manualRefreshPending) return;
    setManualRefreshPending(true);
    try {
      const results = await Promise.all([
        healthQ.refetch(),
        featuresQ.refetch(),
        inboxQ.refetch(),
        contactsQ.refetch(),
        pipelinesQ.refetch(),
        dealsQ.refetch(),
        automationsQ.refetch(),
        broadcastsQ.refetch(),
        templatesQ.refetch(),
        flowsQ.refetch(),
        aiAgentsQ.refetch(),
        dashboardQ.refetch(),
        teamQ.refetch(),
        settingsQ.refetch(),
        apiKeysQ.refetch(),
        webhooksQ.refetch(),
        mcpQ.refetch(),
      ]);
      const failed = results.find((result: any) => result?.error);
      if (failed?.error) throw failed.error;
      setLastRefreshedAt(new Date());
      toast.success(ar ? "تم تحديث بيانات زغلول" : "Zaghloul data refreshed");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : (ar ? "تعذر تحديث بيانات زغلول" : "Unable to refresh Zaghloul data"));
    } finally {
      setManualRefreshPending(false);
    }
  };

  const healthy = healthQ.data?.status === "healthy";
''',
        "zaghloul refresh handler",
    )
    text = replace_once(
        text,
        '''            <div className="flex shrink-0 flex-col items-start gap-3 xl:items-end">
              <div className="flex flex-wrap gap-2"><Badge variant="outline" className="h-10 gap-2 rounded-xl bg-background/80 px-4 font-bold shadow-sm"><Activity className="h-4 w-4 text-emerald-500" />{healthy ? (ar ? "متصل" : "Connected") : (ar ? "جار الفحص" : "Checking")}</Badge><Badge variant="outline" className="h-10 gap-2 rounded-xl bg-background/80 px-4 font-bold shadow-sm"><Sparkles className="h-4 w-4 text-violet-600" />{ar ? "مركز تفاعل موحد" : "Unified engagement"}</Badge></div>
            </div>
''',
        '''            <div className="flex shrink-0 flex-col items-start gap-3 xl:items-end">
              <div className="flex flex-wrap gap-2"><Badge variant="outline" className="h-10 gap-2 rounded-xl bg-background/80 px-4 font-bold shadow-sm"><Activity className="h-4 w-4 text-emerald-500" />{healthy ? (ar ? "متصل" : "Connected") : (ar ? "جار الفحص" : "Checking")}</Badge><Badge variant="outline" className="h-10 gap-2 rounded-xl bg-background/80 px-4 font-bold shadow-sm"><Sparkles className="h-4 w-4 text-violet-600" />{ar ? "مركز تفاعل موحد" : "Unified engagement"}</Badge></div>
              <Button data-ai-staff-refresh="zaghloul-v1" variant="outline" className="h-10 rounded-xl bg-background/70 font-bold" disabled={manualRefreshPending} onClick={refreshZaghloulData}><RefreshCw className={"me-2 h-4 w-4 " + (manualRefreshPending ? "animate-spin" : "")} />{manualRefreshPending ? (ar ? "جار التحديث..." : "Refreshing...") : (ar ? "تحديث البيانات" : "Refresh data")}</Button>
              {lastRefreshedAt ? <p className="text-[11px] font-medium text-muted-foreground">{ar ? "آخر تحديث" : "Last updated"}: {lastRefreshedAt.toLocaleTimeString(ar ? "ar-EG" : "en-US", { hour: "2-digit", minute: "2-digit" })}</p> : null}
            </div>
''',
        "zaghloul refresh button",
    )
    return text


def patch_tara(text: str) -> str:
    text = replace_once(
        text,
        '''    const [testResult, setTestResult] = useState(null);
''',
        '''    const [testResult, setTestResult] = useState(null);
    const [manualRefreshPending, setManualRefreshPending] = useState(false);
    const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);
''',
        "tara refresh state",
    )
    text = replace_once(
        text,
        '''    const refresh = () => Promise.all([utils.tara.dashboard.invalidate(), utils.tara.getSettings.invalidate(), utils.tara.listCampaigns.invalidate(), utils.tara.listQualificationFields.invalidate(), utils.tara.listKnowledge.invalidate(), utils.tara.listFollowupRules.invalidate(), utils.tara.logs.invalidate()]);
''',
        '''    const refresh = () => Promise.all([utils.tara.dashboard.invalidate(), utils.tara.getSettings.invalidate(), utils.tara.listCampaigns.invalidate(), utils.tara.listQualificationFields.invalidate(), utils.tara.listKnowledge.invalidate(), utils.tara.listFollowupRules.invalidate(), utils.tara.logs.invalidate()]);
    const refreshTaraData = async () => {
        if (manualRefreshPending)
            return;
        setManualRefreshPending(true);
        try {
            await utils.tara.invalidate();
            const results = await Promise.all([
                dashboardQ.refetch(),
                settingsQ.refetch(),
                campaignsQ.refetch(),
                usersQ.refetch(),
                crmCampaignsQ.refetch(),
                logsQ.refetch(),
                fieldsQ.refetch(),
                knowledgeQ.refetch(),
                followupsQ.refetch(),
            ]);
            const failed = results.find((result: any) => result?.error);
            if (failed?.error)
                throw failed.error;
            setLastRefreshedAt(new Date());
            toast.success(isRTL ? "تم تحديث بيانات تارا" : "Tara data refreshed");
        }
        catch (error) {
            toast.error(error instanceof Error ? error.message : (isRTL ? "تعذر تحديث بيانات تارا" : "Unable to refresh Tara data"));
        }
        finally {
            setManualRefreshPending(false);
        }
    };
''',
        "tara refresh handler",
    )
    text = replace_once(
        text,
        '''            <Button variant="outline" className="h-10 rounded-xl bg-background px-4 shadow-none" onClick={() => refresh()}>
              <RefreshCw className="ms-2 h-4 w-4" />{isRTL ? "تحديث" : "Refresh"}
            </Button>
''',
        '''            <Button data-ai-staff-refresh="tara-v1" variant="outline" className="h-10 rounded-xl bg-background px-4 shadow-none" disabled={manualRefreshPending} onClick={refreshTaraData}>
              <RefreshCw className={"ms-2 h-4 w-4 " + (manualRefreshPending ? "animate-spin" : "")} />{manualRefreshPending ? (isRTL ? "جار التحديث..." : "Refreshing...") : (isRTL ? "تحديث" : "Refresh")}
            </Button>
            {lastRefreshedAt ? <span className="text-[11px] font-medium text-muted-foreground">{isRTL ? "آخر تحديث" : "Last updated"}: {lastRefreshedAt.toLocaleTimeString(isRTL ? "ar-EG" : "en-US", { hour: "2-digit", minute: "2-digit" })}</span> : null}
''',
        "tara refresh button",
    )
    return text


def patch_felfel(text: str) -> str:
    text = replace_once(
        text,
        '''  const [followUpTopic, setFollowUpTopic] = useState("");

  const platform = useMemo(() => detectPlatform(meetingUrl), [meetingUrl]);
''',
        '''  const [followUpTopic, setFollowUpTopic] = useState("");
  const [manualRefreshPending, setManualRefreshPending] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);

  const platform = useMemo(() => detectPlatform(meetingUrl), [meetingUrl]);
''',
        "felfel refresh state",
    )
    text = replace_once(
        text,
        '''  const archivesQ = trpc.felfel.listArchives.useQuery(
    { clientId: crmClientId || 1 },
    { enabled: Boolean(intelligence && crmClientId), refetchOnWindowFocus: false },
  );
  const archiveMeetingM = trpc.felfel.archiveMeeting.useMutation({
''',
        '''  const archivesQ = trpc.felfel.listArchives.useQuery(
    { clientId: crmClientId || 1 },
    { enabled: Boolean(intelligence && crmClientId), refetchOnWindowFocus: false },
  );

  const refreshFelfelData = async () => {
    if (manualRefreshPending) return;
    setManualRefreshPending(true);
    try {
      const refreshes: Promise<any>[] = [
        healthQ.refetch(),
        capabilitiesQ.refetch(),
        meetingsQ.refetch(),
      ];
      if (meeting) {
        refreshes.push(statusQ.refetch(), transcriptQ.refetch());
      }
      if (intelligence) {
        refreshes.push(crmClientsQ.refetch());
      }
      if (intelligence && crmClientId) {
        refreshes.push(crmDealsQ.refetch(), followUpsQ.refetch(), archivesQ.refetch());
      }
      const results = await Promise.all(refreshes);
      const failed = results.find((result: any) => result?.error);
      if (failed?.error) throw failed.error;
      setLastRefreshedAt(new Date());
      toast.success(ar ? "تم تحديث بيانات فلفل" : "Felfel data refreshed");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : (ar ? "تعذر تحديث بيانات فلفل" : "Unable to refresh Felfel data"));
    } finally {
      setManualRefreshPending(false);
    }
  };

  const archiveMeetingM = trpc.felfel.archiveMeeting.useMutation({
''',
        "felfel refresh handler",
    )
    text = replace_once(
        text,
        '''<p className="text-[11px] font-medium text-muted-foreground">{ar ? "تحديث صحة الخدمة تلقائيًا كل 30 ثانية" : "Service health refreshes automatically every 30 seconds"}</p></div>
''',
        '''<Button data-ai-staff-refresh="felfel-v1" variant="outline" className="h-10 rounded-xl bg-background/70 font-bold" disabled={manualRefreshPending} onClick={refreshFelfelData}><RefreshCw className={"me-2 h-4 w-4 " + (manualRefreshPending ? "animate-spin" : "")} />{manualRefreshPending ? (ar ? "جار التحديث..." : "Refreshing...") : (ar ? "تحديث البيانات" : "Refresh data")}</Button>{lastRefreshedAt ? <p className="text-[11px] font-medium text-muted-foreground">{ar ? "آخر تحديث" : "Last updated"}: {lastRefreshedAt.toLocaleTimeString(ar ? "ar-EG" : "en-US", { hour: "2-digit", minute: "2-digit" })}</p> : null}<p className="text-[11px] font-medium text-muted-foreground">{ar ? "تحديث صحة الخدمة تلقائيًا كل 30 ثانية" : "Service health refreshes automatically every 30 seconds"}</p></div>
''',
        "felfel refresh button",
    )
    return text


PATCHERS = {
    "darwish": patch_darwish,
    "zaghloul": patch_zaghloul,
    "tara": patch_tara,
    "felfel": patch_felfel,
}

MARKERS = {
    "darwish": 'data-ai-staff-refresh="darwish-v1"',
    "zaghloul": 'data-ai-staff-refresh="zaghloul-v1"',
    "tara": 'data-ai-staff-refresh="tara-v1"',
    "felfel": 'data-ai-staff-refresh="felfel-v1"',
}

HANDLERS = {
    "darwish": "refreshDarwishData",
    "zaghloul": "refreshZaghloulData",
    "tara": "refreshTaraData",
    "felfel": "refreshFelfelData",
}


def apply() -> None:
    require_base()
    for name, (path, _) in FILES.items():
        text = read(path)
        if MARKERS[name] in text:
            raise RuntimeError(f"{name}: patch marker already present")
        text = PATCHERS[name](text)
        write(path, text)
        print(f"{name.upper()}_TARGET_BLOB={git_blob(path)}")
    print("APPLY=PASS")


def isolate_handler(text: str, name: str) -> str:
    handler = HANDLERS[name]
    start = text.index(f"const {handler} = async")
    end_marker = "\n    };" if name == "tara" else "\n  };"
    end = text.find(end_marker, start)
    if end < 0:
        raise RuntimeError(f"{name}: could not isolate refresh handler")
    return text[start:end]


def verify() -> None:
    for name, (path, _) in FILES.items():
        text = read(path)
        if text.count(MARKERS[name]) != 1:
            raise RuntimeError(f"{name}: expected one refresh marker")
        if text.count(f"const {HANDLERS[name]} = async") != 1:
            raise RuntimeError(f"{name}: missing manual refresh handler")
        block = isolate_handler(text, name)
        if ".mutate(" in block:
            raise RuntimeError(f"{name}: manual refresh handler must not invoke mutations")
        if "lastRefreshedAt" not in text or "manualRefreshPending" not in text:
            raise RuntimeError(f"{name}: refresh feedback state missing")

    darwish = read(FILES["darwish"][0])
    for preserved in ['data-darwish-workspace="supervisor-v3"', "DarwishLimitedAutomationCard", "refreshActionsM", "approveActionM", "executeActionM"]:
        if preserved not in darwish:
            raise RuntimeError(f"darwish: preserved marker missing: {preserved}")

    zaghloul = read(FILES["zaghloul"][0])
    if 'data-zaghloul-workspace="grouped-nav-v2"' not in zaghloul:
        raise RuntimeError("zaghloul: grouped navigation marker missing")

    tara = read(FILES["tara"][0])
    if 'data-tara-workspace="control-center-v2"' not in tara:
        raise RuntimeError("tara: control center marker missing")
    if "const refresh = () => Promise.all(" not in tara:
        raise RuntimeError("tara: silent post-mutation refresh helper missing")

    felfel = read(FILES["felfel"][0])
    if 'data-felfel-uxui="reference-v7"' not in felfel:
        raise RuntimeError("felfel: V7 marker missing")
    for mutation in ["createMeetingM", "leaveMeetingM", "analyzeMeetingM", "createApprovedTasksM", "createFollowUpM", "archiveMeetingM"]:
        if mutation not in felfel:
            raise RuntimeError(f"felfel: preserved mutation missing: {mutation}")

    for name, (path, _) in FILES.items():
        print(f"{name.upper()}_BLOB={git_blob(path)}")
    print("VERIFY=PASS")


def check() -> None:
    require_base()
    for name, (path, expected) in FILES.items():
        text = read(path)
        if MARKERS[name] in text:
            raise RuntimeError(f"{name}: target marker already present on guarded base")
        print(f"{name.upper()}_BASE_BLOB={expected}")
    print("CHECK=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            check()
        elif args.apply:
            apply()
        else:
            verify()
        return 0
    except Exception as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
