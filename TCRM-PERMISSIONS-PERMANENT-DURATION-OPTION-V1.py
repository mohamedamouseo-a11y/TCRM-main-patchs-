#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

PATCH_NAME = "TCRM_PERMISSIONS_PERMANENT_DURATION_OPTION_V1"
EXPECTED_MAIN_COMMIT = "a359b82be80095e25af94ab7571f086778586d63"
EXPECTED_BLOBS = {
    "client/src/pages/RolesPermissions.tsx": "5fac77f7e108c69964b2bac6d432b8deb4661ec8",
}
TARGETS = tuple(EXPECTED_BLOBS)
BACKUP_DIR = Path(".tcrm-patch-backups") / PATCH_NAME


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"ANCHOR_FAIL={label}:expected_1_found_{count}")
    return text.replace(old, new, 1)


def run_git_diff_check() -> None:
    proc = subprocess.run(
        ["git", "diff", "--check", "--", *TARGETS],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError("GIT_DIFF_CHECK_FAIL=" + proc.stdout.strip().replace("\n", " | "))


def restore_backups() -> None:
    for rel in TARGETS:
        src = BACKUP_DIR / rel
        dst = Path(rel)
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def main() -> int:
    root = Path.cwd()
    for rel, expected in EXPECTED_BLOBS.items():
        path = root / rel
        if not path.is_file():
            print("PATCH=FAIL")
            print(f"ERROR=MISSING_SOURCE:{rel}")
            return 2
        actual = git_blob_sha(path.read_bytes())
        if actual != expected:
            print("PATCH=STOP")
            print(f"SOURCE_GUARD_FAIL={rel}")
            print(f"EXPECTED_BLOB={expected}")
            print(f"ACTUAL_BLOB={actual}")
            print("ERROR=SOURCE_CHANGED_DO_NOT_FORCE")
            return 3

    rel = "client/src/pages/RolesPermissions.tsx"
    original = (root / rel).read_text(encoding="utf-8")
    updated = original

    updated = replace_once(
        updated,
        '''type EffectState = "inherit" | "allow" | "deny";
type PermissionDraft = { effect: EffectState; dataScope: string; scopeConfig?: Record<string, unknown> | null; startsAt?: string | null; expiresAt?: string | null; reason?: string | null };
type FieldEditorTarget = "role" | "user";''',
        '''type EffectState = "inherit" | "allow" | "deny";
type PermissionDurationMode = "permanent" | "temporary";
type PermissionDraft = { effect: EffectState; dataScope: string; scopeConfig?: Record<string, unknown> | null; startsAt?: string | null; expiresAt?: string | null; reason?: string | null; durationMode?: PermissionDurationMode };
type FieldEditorTarget = "role" | "user";''',
        "permission_duration_type",
    )

    updated = replace_once(
        updated,
        '''        startsAt: toDateTimeLocalInput(item.startsAt),
        expiresAt: toDateTimeLocalInput(item.expiresAt),
        reason: item.reason == null ? "" : String(item.reason),''',
        '''        startsAt: toDateTimeLocalInput(item.startsAt),
        expiresAt: toDateTimeLocalInput(item.expiresAt),
        reason: item.reason == null ? "" : String(item.reason),
        durationMode: item.startsAt || item.expiresAt ? "temporary" : "permanent",''',
        "load_duration_mode",
    )

    updated = replace_once(
        updated,
        '''      const startsAt = fromDateTimeLocalInput(v.startsAt);
      const expiresAt = fromDateTimeLocalInput(v.expiresAt);
      if (startsAt && expiresAt && expiresAt <= startsAt) {
        toast.error(isRTL ? `وقت انتهاء ${permissionKey} يجب أن يكون بعد وقت البداية` : `${permissionKey}: expiry must be after start`);
        return;
      }
      entries.push({
        permissionKey,
        effect: v.effect as "allow" | "deny",
        dataScope: (v.effect === "deny" ? "none" : v.dataScope) as any,
        scopeConfig: v.scopeConfig ?? null,
        startsAt,
        expiresAt,
        reason: v.reason?.trim() || null,
      });''',
        '''      const durationMode: PermissionDurationMode = v.durationMode ?? (v.startsAt || v.expiresAt ? "temporary" : "permanent");
      const startsAt = durationMode === "temporary" ? fromDateTimeLocalInput(v.startsAt) : null;
      const expiresAt = durationMode === "temporary" ? fromDateTimeLocalInput(v.expiresAt) : null;
      if (durationMode === "temporary" && !expiresAt) {
        toast.error(isRTL ? `حدد وقت انتهاء ${permissionKey} أو اختر "مستمرة بدون انتهاء"` : `${permissionKey}: choose an expiry or select Permanent (no expiry)`);
        return;
      }
      if (startsAt && expiresAt && expiresAt <= startsAt) {
        toast.error(isRTL ? `وقت انتهاء ${permissionKey} يجب أن يكون بعد وقت البداية` : `${permissionKey}: expiry must be after start`);
        return;
      }
      entries.push({
        permissionKey,
        effect: v.effect as "allow" | "deny",
        dataScope: (v.effect === "deny" ? "none" : v.dataScope) as any,
        scopeConfig: v.scopeConfig ?? null,
        startsAt,
        expiresAt,
        reason: v.reason?.trim() || null,
      });''',
        "save_duration_mode",
    )

    updated = replace_once(
        updated,
        '''                  <div className="mt-3 rounded-lg bg-amber-50 border border-amber-200 p-2 text-xs text-amber-700">{isRTL ? "استثناءات المستخدم تتفوق على صلاحيات الدور. يمكن تحديد بداية ونهاية مؤقتة لكل استثناء؛ اتركهما فارغين ليكون دائمًا. Deny = بدون نطاق، و Inherit = لا override." : "User overrides take precedence over role permissions. Each override can have an optional start and expiry; leave both blank for permanent access. Deny = none scope; Inherit = no override."}</div>''',
        '''                  <div className="mt-3 rounded-lg bg-amber-50 border border-amber-200 p-2 text-xs text-amber-700">{isRTL ? "استثناءات المستخدم تتفوق على صلاحيات الدور. مدة الصلاحية اختيارية: اختر «مستمرة بدون انتهاء» للصلاحية الدائمة، أو «مؤقتة» وحدد وقت الانتهاء. Deny = بدون نطاق، و Inherit = لا override." : "User overrides take precedence over role permissions. Duration is optional: choose Permanent (no expiry) for continuous access, or Temporary and set an expiry. Deny = none scope; Inherit = no override."}</div>''',
        "duration_help_text",
    )

    updated = replace_once(
        updated,
        '''                    const state = userDraft[key] || { effect: "inherit", dataScope: "none", startsAt: "", expiresAt: "", reason: "" };
                    const now = Date.now();
                    const startMs = state.startsAt ? new Date(state.startsAt).getTime() : null;
                    const expiryMs = state.expiresAt ? new Date(state.expiresAt).getTime() : null;
                    const timingStatus = state.effect === "inherit" ? "inherit" : expiryMs != null && expiryMs <= now ? "expired" : startMs != null && startMs > now ? "scheduled" : state.startsAt || state.expiresAt ? "active" : "permanent";''',
        '''                    const state = userDraft[key] || { effect: "inherit", dataScope: "none", startsAt: "", expiresAt: "", reason: "", durationMode: "permanent" as PermissionDurationMode };
                    const durationMode: PermissionDurationMode = state.durationMode ?? (state.startsAt || state.expiresAt ? "temporary" : "permanent");
                    const now = Date.now();
                    const startMs = state.startsAt ? new Date(state.startsAt).getTime() : null;
                    const expiryMs = state.expiresAt ? new Date(state.expiresAt).getTime() : null;
                    const timingStatus = state.effect === "inherit" ? "inherit" : durationMode === "permanent" ? "permanent" : expiryMs != null && expiryMs <= now ? "expired" : startMs != null && startMs > now ? "scheduled" : "active";''',
        "timing_status_duration_mode",
    )

    updated = replace_once(
        updated,
        '''                      {state.effect !== "inherit" && <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_minmax(180px,1fr)_auto] gap-3 items-end rounded-lg bg-muted/25 p-3">
                        <div><Label className="text-xs">{isRTL ? "يبدأ في" : "Starts at"}</Label><Input type="datetime-local" value={state.startsAt || ""} onChange={e => setUserPermission(key, { startsAt: e.target.value })} className="mt-1" /></div>
                        <div><Label className="text-xs">{isRTL ? "ينتهي في" : "Expires at"}</Label><Input type="datetime-local" value={state.expiresAt || ""} onChange={e => setUserPermission(key, { expiresAt: e.target.value })} className="mt-1" /></div>
                        <div><Label className="text-xs">{isRTL ? "سبب / ملاحظة" : "Reason / note"}</Label><Input value={state.reason || ""} onChange={e => setUserPermission(key, { reason: e.target.value })} maxLength={500} placeholder={isRTL ? "اختياري" : "Optional"} className="mt-1" /></div>
                        <Badge variant={timingStatus === "expired" ? "destructive" : timingStatus === "scheduled" ? "secondary" : "outline"} className="mb-2 w-fit">{timingLabel}</Badge>
                      </div>}''',
        '''                      {state.effect !== "inherit" && <div className={`grid grid-cols-1 ${durationMode === "temporary" ? "md:grid-cols-[220px_1fr_1fr_minmax(180px,1fr)_auto]" : "md:grid-cols-[240px_minmax(180px,1fr)_auto]"} gap-3 items-end rounded-lg bg-muted/25 p-3`}>
                        <div>
                          <Label className="text-xs">{isRTL ? "مدة الصلاحية" : "Access duration"}</Label>
                          <Select value={durationMode} onValueChange={(value: PermissionDurationMode) => setUserPermission(key, value === "permanent" ? { durationMode: value, startsAt: "", expiresAt: "" } : { durationMode: value })}>
                            <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="permanent">{isRTL ? "مستمرة بدون انتهاء" : "Permanent (no expiry)"}</SelectItem>
                              <SelectItem value="temporary">{isRTL ? "مؤقتة" : "Temporary"}</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        {durationMode === "temporary" && <>
                          <div><Label className="text-xs">{isRTL ? "يبدأ في (اختياري)" : "Starts at (optional)"}</Label><Input type="datetime-local" value={state.startsAt || ""} onChange={e => setUserPermission(key, { startsAt: e.target.value })} className="mt-1" /></div>
                          <div><Label className="text-xs">{isRTL ? "ينتهي في" : "Expires at"}</Label><Input type="datetime-local" value={state.expiresAt || ""} onChange={e => setUserPermission(key, { expiresAt: e.target.value })} className="mt-1" /></div>
                        </>}
                        <div><Label className="text-xs">{isRTL ? "سبب / ملاحظة" : "Reason / note"}</Label><Input value={state.reason || ""} onChange={e => setUserPermission(key, { reason: e.target.value })} maxLength={500} placeholder={isRTL ? "اختياري" : "Optional"} className="mt-1" /></div>
                        <Badge variant={timingStatus === "expired" ? "destructive" : timingStatus === "scheduled" ? "secondary" : "outline"} className="mb-2 w-fit">{timingLabel}</Badge>
                      </div>}''',
        "duration_selector_ui",
    )

    must_have = [
        'type PermissionDurationMode = "permanent" | "temporary";',
        'durationMode: item.startsAt || item.expiresAt ? "temporary" : "permanent"',
        'choose an expiry or select Permanent (no expiry)',
        'value="permanent"',
        'value="temporary"',
        'مستمرة بدون انتهاء',
        'durationMode === "permanent" ? "permanent"',
    ]
    for marker in must_have:
        if marker not in updated:
            raise RuntimeError(f"VERIFY_MARKER_FAIL={marker}")

    if 'startsAt: durationMode === "temporary"' in updated:
        raise RuntimeError("VERIFY_FAIL=UNEXPECTED_INLINE_DATE_MUTATION")

    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    for target in TARGETS:
        src = root / target
        dst = root / BACKUP_DIR / target
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    try:
        (root / rel).write_text(updated, encoding="utf-8")
        run_git_diff_check()
    except Exception:
        restore_backups()
        raise

    print("PATCH=PASS")
    print("PATCH_NAME=" + PATCH_NAME)
    print("BASE_MAIN_COMMIT=" + EXPECTED_MAIN_COMMIT)
    print("FILES_CHANGED=" + rel)
    print("DEFAULT_DURATION=PERMANENT_NO_EXPIRY")
    print("TEMPORARY_EXPIRY=OPTIONAL_MODE_REQUIRED_DATE")
    print("BACKEND_CHANGE=NO")
    print("DB_MIGRATION=NO")
    print("PERMISSION_ENGINE=UNCHANGED")
    print("PERMISSION_AUDIT=UNCHANGED")
    print("BACKUP=" + str(BACKUP_DIR))
    print("GIT_DIFF_CHECK=PASS")
    print("ERROR=NONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("PATCH=FAIL")
        print("ERROR=" + str(exc).replace("\n", " | "))
        raise SystemExit(1)
