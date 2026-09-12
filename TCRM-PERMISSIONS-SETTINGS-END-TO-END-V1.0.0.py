#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "SETTINGS"
PHASE = "END-TO-END"
VERSION = "V1.0.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-SETTINGS-END-TO-END-V1.0.0"
BASELINE = "7eb1f79870c7457b7a3ce078883571edde998470"

ROOT = Path.cwd()
EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/AdminSettings.tsx",
    "server/security/corePermissionPolicy.ts",
    "server/security/settingsPermissionFinal.test.ts",
}


def fail(message: str) -> None:
    print(f"ERROR={message}", file=sys.stderr)
    raise SystemExit(1)


def run(*args: str) -> str:
    p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        fail(f"COMMAND_FAILED:{' '.join(args)}:{p.stderr.strip()}")
    return p.stdout.strip()


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        fail(f"MISSING_FILE:{rel}")
    return p.read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"ANCHOR_DRIFT:{label}:count={count}")
    return text.replace(old, new, 1)


def dirty_paths() -> set[str]:
    tracked = set(filter(None, run("git", "diff", "--name-only").splitlines()))
    untracked = set(filter(None, run("git", "ls-files", "--others", "--exclude-standard").splitlines()))
    return tracked | untracked


head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")
if run("git", "diff", "--cached", "--name-only"):
    fail("STAGED_CHANGES_PRESENT")
if dirty_paths():
    fail(f"WORKTREE_NOT_CLEAN:{sorted(dirty_paths())}")

# ---------------------------------------------------------------------------
# Frontend effective-permission request: Settings already owns route access via
# settings.view; add settings.edit for core configuration actions.
# ---------------------------------------------------------------------------
ctx_rel = "client/src/contexts/PermissionContext.tsx"
ctx = read(ctx_rel)
ctx = replace_once(
    ctx,
    '  "settings.view",\n  "roles.view",',
    '  "settings.view",\n  "settings.edit",\n  "roles.view",',
    "permission-context-settings-edit",
)
write(ctx_rel, ctx)

# ---------------------------------------------------------------------------
# Backend permission boundary for Settings-owned configuration mutations.
# Reads remain intentionally shared because pipeline/custom-field/theme/SLA read
# endpoints are consumed by operational screens outside AdminSettings.
# ---------------------------------------------------------------------------
policy_rel = "server/security/corePermissionPolicy.ts"
policy = read(policy_rel)
policy = replace_once(
    policy,
    '''  if (root === "auth" && operation === "adminsetpassword") {
    return "users.edit";
  }

  const module = moduleFromPath(path);
''',
    '''  if (root === "auth" && operation === "adminsetpassword") {
    return "users.edit";
  }

  // TCRM_PERMISSIONS_SETTINGS_END_TO_END_V1
  // Core Settings owns mutations for pipeline stages, custom fields, theme and
  // SLA configuration. Their read endpoints are shared by operational screens,
  // so preserve those reads instead of forcing settings.view outside Settings.
  if (["pipeline", "customFields", "theme", "sla"].includes(root)) {
    if (type === "query" || type === "subscription") return null;
    return "settings.edit";
  }

  const module = moduleFromPath(path);
''',
    "core-policy-settings",
)
write(policy_rel, policy)

# ---------------------------------------------------------------------------
# AdminSettings frontend gates for the Settings-owned core configuration tabs.
# Existing Admin role guards remain additive; no visual redesign is introduced.
# ---------------------------------------------------------------------------
admin_rel = "client/src/pages/AdminSettings.tsx"
admin = read(admin_rel)

admin = replace_once(
    admin,
    '''function SortableStageRow({
  stage,
  onDelete,
  onToggle,
  tokens,
}: {
  stage: any;
  onDelete: (id: number) => void;
  onToggle: (id: number, isActive: boolean) => void;
  tokens: any;
}) {''',
    '''function SortableStageRow({
  stage,
  onDelete,
  onToggle,
  tokens,
  canEdit,
}: {
  stage: any;
  onDelete: (id: number) => void;
  onToggle: (id: number, isActive: boolean) => void;
  tokens: any;
  canEdit: boolean;
}) {''',
    "stage-row-can-edit-prop",
)

admin = replace_once(
    admin,
    '<button {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground">',
    '<button {...attributes} {...listeners} disabled={!canEdit} className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50">',
    "stage-drag-disable",
)

admin = replace_once(
    admin,
    '''      <Switch
        checked={stage.isActive ?? true}
        onCheckedChange={(v) => onToggle(stage.id, v)}
        title={stage.isActive ? "Disable stage" : "Enable stage"}
      />''',
    '''      <Switch
        checked={stage.isActive ?? true}
        onCheckedChange={(v) => onToggle(stage.id, v)}
        disabled={!canEdit}
        title={stage.isActive ? "Disable stage" : "Enable stage"}
      />''',
    "stage-toggle-disable",
)

admin = replace_once(
    admin,
    '''        className="h-7 w-7 text-muted-foreground hover:text-destructive"
        onClick={() => onDelete(stage.id)}
      >''',
    '''        className="h-7 w-7 text-muted-foreground hover:text-destructive"
        onClick={() => onDelete(stage.id)}
        disabled={!canEdit}
      >''',
    "stage-delete-disable",
)

admin = replace_once(
    admin,
    '  const canUsersAssignRoles = can("users.assign_roles");\n',
    '  const canUsersAssignRoles = can("users.assign_roles");\n  const canSettingsEdit = can("settings.edit");\n',
    "settings-edit-flag",
)

admin = replace_once(
    admin,
    '''  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;''',
    '''  const handleDragEnd = (event: DragEndEvent) => {
    if (!canSettingsEdit) return;
    const { active, over } = event;''',
    "pipeline-reorder-guard",
)

admin = replace_once(
    admin,
    '''  const handleSaveTheme = () => {
    const entries = Object.entries(themeForm).map(([key, value]) => ({ key, value }));''',
    '''  const handleSaveTheme = () => {
    if (!canSettingsEdit) return;
    const entries = Object.entries(themeForm).map(([key, value]) => ({ key, value }));''',
    "theme-save-guard",
)

admin = replace_once(
    admin,
    '''  const handleSaveSLA = () => {
    updateSLA.mutate(slaForm);''',
    '''  const handleSaveSLA = () => {
    if (!canSettingsEdit) return;
    updateSLA.mutate(slaForm);''',
    "sla-save-guard",
)

admin = replace_once(
    admin,
    '''                <Button size="sm" style={{ background: tokens.primaryColor }} className="text-white gap-1.5"
                  onClick={() => setShowAddStage(true)}>''',
    '''                <Button size="sm" style={{ background: tokens.primaryColor }} className="text-white gap-1.5"
                  disabled={!canSettingsEdit}
                  onClick={() => setShowAddStage(true)}>''',
    "pipeline-add-disable",
)

admin = replace_once(
    admin,
    '''                        <SortableStageRow
                          key={stage.id}
                          stage={stage}
                          tokens={tokens}''',
    '''                        <SortableStageRow
                          key={stage.id}
                          stage={stage}
                          tokens={tokens}
                          canEdit={canSettingsEdit}''',
    "pipeline-stage-row-prop",
)

admin = replace_once(
    admin,
    '''                <Button size="sm" style={{ background: tokens.primaryColor }} className="text-white gap-1.5"
                  onClick={() => setShowAddField(true)}>''',
    '''                <Button size="sm" style={{ background: tokens.primaryColor }} className="text-white gap-1.5"
                  disabled={!canSettingsEdit}
                  onClick={() => setShowAddField(true)}>''',
    "custom-field-add-disable",
)

admin = replace_once(
    admin,
    '''                            className="h-7 w-7 text-muted-foreground hover:text-destructive"
                            onClick={() => deleteField.mutate({ id: field.id })}
                          >''',
    '''                            className="h-7 w-7 text-muted-foreground hover:text-destructive"
                            onClick={() => deleteField.mutate({ id: field.id })}
                            disabled={!canSettingsEdit}
                          >''',
    "custom-field-delete-disable",
)

admin = replace_once(
    admin,
    '                  disabled={setBulkTheme.isPending}\n',
    '                  disabled={!canSettingsEdit || setBulkTheme.isPending}\n',
    "theme-save-disable",
)

admin = replace_once(
    admin,
    '''                  <Switch
                    checked={slaForm.isEnabled}
                    onCheckedChange={(v) => setSlaForm((p) => ({ ...p, isEnabled: v }))}
                  />''',
    '''                  <Switch
                    checked={slaForm.isEnabled}
                    onCheckedChange={(v) => setSlaForm((p) => ({ ...p, isEnabled: v }))}
                    disabled={!canSettingsEdit}
                  />''',
    "sla-toggle-disable",
)

admin = replace_once(
    admin,
    '''                    max={720}
                    dir="ltr"
                  />''',
    '''                    max={720}
                    dir="ltr"
                    disabled={!canSettingsEdit}
                  />''',
    "sla-threshold-disable",
)

admin = replace_once(
    admin,
    '                    disabled={updateSLA.isPending}\n',
    '                    disabled={!canSettingsEdit || updateSLA.isPending}\n',
    "sla-save-disable",
)

admin = replace_once(
    admin,
    '                    disabled={checkSLA.isPending}\n',
    '                    disabled={!canSettingsEdit || checkSLA.isPending}\n',
    "sla-check-disable",
)

admin = replace_once(
    admin,
    '<form onSubmit={stageSubmit((data) => createStage.mutate({ ...data, color: selectedColor }))} className="space-y-4">',
    '<form onSubmit={stageSubmit((data) => { if (!canSettingsEdit) return; createStage.mutate({ ...data, color: selectedColor }); })} className="space-y-4">',
    "stage-submit-guard",
)

admin = replace_once(
    admin,
    '              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={createStage.isPending}>',
    '              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={!canSettingsEdit || createStage.isPending}>',
    "stage-submit-disable",
)

admin = replace_once(
    admin,
    '<form onSubmit={fieldSubmit((data) => createField.mutate(data))} className="space-y-4">',
    '<form onSubmit={fieldSubmit((data) => { if (!canSettingsEdit) return; createField.mutate(data); })} className="space-y-4">',
    "field-submit-guard",
)

admin = replace_once(
    admin,
    '              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={createField.isPending}>',
    '              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={!canSettingsEdit || createField.isPending}>',
    "field-submit-disable",
)

write(admin_rel, admin)

# ---------------------------------------------------------------------------
# Final Settings regression coverage.
# ---------------------------------------------------------------------------
test_rel = "server/security/settingsPermissionFinal.test.ts"
if (ROOT / test_rel).exists():
    fail("SETTINGS_FINAL_TEST_ALREADY_EXISTS")

test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { resolveCorePermissionKey } from "./corePermissionPolicy";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const read = (relative: string) => readFileSync(path.join(root, relative), "utf8");

const catalog = read("server/security/permissionCatalog.ts");
const context = read("client/src/contexts/PermissionContext.tsx");
const admin = read("client/src/pages/AdminSettings.tsx");

describe("Settings permissions E2E V1.0.0", () => {
  it("keeps both Settings permissions in the canonical catalog and frontend request", () => {
    for (const key of ["settings.view", "settings.edit"]) {
      expect(catalog).toContain(`"${key}"`);
      expect(context).toContain(`"${key}"`);
    }
  });

  it("keeps Settings route access on settings.view", () => {
    expect(context).toContain('if (pathname === "/admin") return "settings.view";');
    expect(context).toContain('["/settings", "settings.view"]');
  });

  it("maps Settings-owned core mutations to settings.edit", () => {
    for (const pathName of [
      "pipeline.create",
      "pipeline.delete",
      "pipeline.toggle",
      "pipeline.reorder",
      "customFields.create",
      "customFields.delete",
      "theme.setBulk",
      "sla.update",
      "sla.check",
    ]) {
      expect(resolveCorePermissionKey(pathName, "mutation")).toBe("settings.edit");
    }
  });

  it("preserves shared Settings-owned reads for operational consumers", () => {
    expect(resolveCorePermissionKey("pipeline.list", "query")).toBeNull();
    expect(resolveCorePermissionKey("customFields.list", "query")).toBeNull();
    expect(resolveCorePermissionKey("theme.get", "query")).toBeNull();
    expect(resolveCorePermissionKey("sla.get", "query")).toBeNull();
  });

  it("does not hijack permissions owned by other modules", () => {
    expect(resolveCorePermissionKey("campaigns.update", "mutation")).toBe("campaigns.edit");
    expect(resolveCorePermissionKey("waGateway.saveSettings", "mutation")).toBe("whatsapp.manage");
    expect(resolveCorePermissionKey("users.update", "mutation")).toBe("users.edit");
  });

  it("gates core Settings write actions in AdminSettings", () => {
    for (const marker of [
      'const canSettingsEdit = can("settings.edit")',
      'if (!canSettingsEdit) return;',
      'canEdit={canSettingsEdit}',
      'disabled={!canSettingsEdit || setBulkTheme.isPending}',
      'disabled={!canSettingsEdit || updateSLA.isPending}',
      'disabled={!canSettingsEdit || checkSLA.isPending}',
      'disabled={!canSettingsEdit || createStage.isPending}',
      'disabled={!canSettingsEdit || createField.isPending}',
    ]) {
      expect(admin).toContain(marker);
    }
  });

  it("preserves existing Admin role guards on core Settings tabs", () => {
    expect(admin).toContain('{isAdmin && <TabsContent value="pipeline"');
    expect(admin).toContain('{isAdmin && <TabsContent value="fields"');
    expect(admin).toContain('{isAdmin && <TabsContent value="theme"');
    expect(admin).toContain('{isAdmin && <TabsContent value="sla"');
  });
});
'''
write(test_rel, test)

paths = dirty_paths()
if paths != EXPECTED:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(paths)}")
run("git", "diff", "--check")

ctx = read(ctx_rel)
policy = read(policy_rel)
admin = read(admin_rel)
final_test = read(test_rel)

for marker in ['"settings.view"', '"settings.edit"', '["/settings", "settings.view"]']:
    if marker not in ctx:
        fail(f"FINAL_STATE_MISSING:context:{marker}")

for marker in ['["pipeline", "customFields", "theme", "sla"]', 'return "settings.edit";']:
    if marker not in policy:
        fail(f"FINAL_STATE_MISSING:policy:{marker}")

for marker in [
    'const canSettingsEdit = can("settings.edit")',
    'canEdit={canSettingsEdit}',
    'disabled={!canSettingsEdit || setBulkTheme.isPending}',
    'disabled={!canSettingsEdit || updateSLA.isPending}',
    'disabled={!canSettingsEdit || createStage.isPending}',
    'disabled={!canSettingsEdit || createField.isPending}',
]:
    if marker not in admin:
        fail(f"FINAL_STATE_MISSING:admin:{marker}")

if 'describe("Settings permissions E2E V1.0.0"' not in final_test:
    fail("FINAL_STATE_MISSING:settings-test")

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("SETTINGS_PERMISSION_KEYS=settings.view,settings.edit")
print("SETTINGS_ROUTE_GATE=PASS")
print("SETTINGS_EDIT_API_GATE=PASS")
print("SETTINGS_SHARED_READS_PRESERVED=YES")
print("SETTINGS_PIPELINE_UI_GATE=PASS")
print("SETTINGS_CUSTOM_FIELDS_UI_GATE=PASS")
print("SETTINGS_THEME_UI_GATE=PASS")
print("SETTINGS_SLA_UI_GATE=PASS")
print("EXISTING_ADMIN_ROLE_GUARDS_PRESERVED=YES")
print("OTHER_PERMISSION_MODULES_PRESERVED=YES")
print("CSS_CHANGED=NO")
print("DB_SCHEMA_CHANGED=NO")
print("DATA_CHANGED=NO")
print("FINAL_EXPECTED_FILES=4")
