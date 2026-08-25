#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess

ROOT = pathlib.Path.cwd()

EXPECTED_SERVER_BLOBS = {
    pathlib.Path("client/src/pages/DarwishPage.tsx"): "2779e41b24972ae96b69f898d53e04139bfa9d4e",
    pathlib.Path("client/src/pages/ZaghloulV5Page.tsx"): "d1f97d0ea81390b0df93828acbf1facfa41e5ec0",
    pathlib.Path("client/src/pages/TaraAgentPage.tsx"): "1354a816f999330e81486038232ee8c93df99cac",
    pathlib.Path("client/src/pages/FelfelPage.tsx"): "ea2fee98503574dddac508080815166a3ea7fe22",
}

FELFEL = pathlib.Path("client/src/pages/FelfelPage.tsx")
MARKER = "TCRM_FELFEL_REFRESH_COMPLETION_V1"

OLD_HANDLER = '''  const refreshFelfelData = async () => {
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
'''

NEW_HANDLER = '''  // TCRM_FELFEL_REFRESH_COMPLETION_V1
  const refreshFelfelData = async () => {
    if (manualRefreshPending) return;
    setManualRefreshPending(true);
    try {
      type RefreshOutcome = { label: string; ok: boolean; timedOut?: boolean; error?: unknown };
      const boundedRefetch = async (label: string, request: Promise<any>): Promise<RefreshOutcome> => {
        let timer: ReturnType<typeof setTimeout> | undefined;
        try {
          return await Promise.race([
            request
              .then((result: any) => result?.error
                ? ({ label, ok: false, error: result.error } as RefreshOutcome)
                : ({ label, ok: true } as RefreshOutcome))
              .catch((error: unknown) => ({ label, ok: false, error } as RefreshOutcome)),
            new Promise<RefreshOutcome>((resolve) => {
              timer = setTimeout(() => resolve({ label, ok: false, timedOut: true }), 6_000);
            }),
          ]);
        } finally {
          if (timer) clearTimeout(timer);
        }
      };

      const refreshes: Array<[string, Promise<any>]> = [
        ["health", healthQ.refetch()],
        ["capabilities", capabilitiesQ.refetch()],
        ["meetings", meetingsQ.refetch()],
      ];
      if (meeting) {
        refreshes.push(["meeting-status", statusQ.refetch()], ["transcript", transcriptQ.refetch()]);
      }
      if (intelligence) {
        refreshes.push(["crm-clients", crmClientsQ.refetch()]);
      }
      if (intelligence && crmClientId) {
        refreshes.push(
          ["crm-deals", crmDealsQ.refetch()],
          ["crm-followups", followUpsQ.refetch()],
          ["archives", archivesQ.refetch()],
        );
      }

      const outcomes = await Promise.all(refreshes.map(([label, request]) => boundedRefetch(label, request)));
      const succeeded = outcomes.filter((item) => item.ok);
      const failed = outcomes.filter((item) => !item.ok);

      if (succeeded.length === 0) {
        const timedOut = failed.some((item) => item.timedOut);
        throw new Error(timedOut
          ? (ar ? "انتهت مهلة تحديث بيانات فلفل" : "Felfel data refresh timed out")
          : (ar ? "تعذر تحديث بيانات فلفل" : "Unable to refresh Felfel data"));
      }

      setLastRefreshedAt(new Date());
      if (failed.length > 0) {
        toast.warning(ar
          ? `تم تحديث بيانات فلفل الأساسية مع ${failed.length} تحذير مؤقت`
          : `Felfel core data refreshed with ${failed.length} temporary warning${failed.length === 1 ? "" : "s"}`);
      } else {
        toast.success(ar ? "تم تحديث بيانات فلفل" : "Felfel data refreshed");
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : (ar ? "تعذر تحديث بيانات فلفل" : "Unable to refresh Felfel data"));
    } finally {
      setManualRefreshPending(false);
    }
  };
'''


def git_blob(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def check_server_state() -> None:
    failures: list[str] = []
    for path, expected in EXPECTED_SERVER_BLOBS.items():
        actual = git_blob(path)
        if actual != expected:
            failures.append(f"{path}: expected {expected}, got {actual}")
    if failures:
        raise RuntimeError("Server Phase 6 target state mismatch:\n" + "\n".join(failures))


def apply() -> None:
    check_server_state()
    path = ROOT / FELFEL
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        raise RuntimeError("Corrective marker already present")
    count = text.count(OLD_HANDLER)
    if count != 1:
        raise RuntimeError(f"Expected exactly one Phase 6 Felfel refresh handler, found {count}")
    text = text.replace(OLD_HANDLER, NEW_HANDLER, 1)
    path.write_text(text, encoding="utf-8")
    print(f"FELFEL_CORRECTED_BLOB={git_blob(FELFEL)}")
    print("APPLY=PASS")


def verify() -> None:
    text = (ROOT / FELFEL).read_text(encoding="utf-8")
    required = [
        MARKER,
        'data-ai-staff-refresh="felfel-v1"',
        "const refreshFelfelData = async",
        "boundedRefetch",
        "Promise.race",
        "6_000",
        "setManualRefreshPending(false)",
        "setLastRefreshedAt(new Date())",
        "createMeetingM",
        "leaveMeetingM",
        "analyzeMeetingM",
        "createApprovedTasksM",
        "createFollowUpM",
        "archiveMeetingM",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError("Missing required markers: " + ", ".join(missing))
    start = text.index("const refreshFelfelData = async")
    end = text.index("\n  const archiveMeetingM", start)
    handler = text[start:end]
    if ".mutate(" in handler:
        raise RuntimeError("Manual Felfel refresh handler contains mutation call")
    if "Promise.all(refreshes)" in handler:
        raise RuntimeError("Unbounded Phase 6 Promise.all refresh pattern still present")
    print(f"FELFEL_CORRECTED_BLOB={git_blob(FELFEL)}")
    print("VERIFY=PASS")


def check() -> None:
    check_server_state()
    text = (ROOT / FELFEL).read_text(encoding="utf-8")
    if MARKER in text:
        raise RuntimeError("Corrective patch already applied")
    if text.count(OLD_HANDLER) != 1:
        raise RuntimeError("Expected Phase 6 Felfel refresh handler not found exactly once")
    print("CHECK=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
    elif args.apply:
        apply()
    else:
        verify()


if __name__ == "__main__":
    main()
