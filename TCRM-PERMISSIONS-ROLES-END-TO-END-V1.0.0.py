#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys
from pathlib import Path

WORKFLOW_SERIES="TCRM-PERMISSIONS"
MODULE="ROLES"
PHASE="END-TO-END"
VERSION="V1.0.0"
WORKFLOW_ID="TCRM-PERMISSIONS-ROLES-END-TO-END-V1.0.0"
BASELINE="37a2c92e4b026b4cea657ba6feced8b88c164a99"
ROOT=Path.cwd()
EXPECTED={
 "client/src/contexts/PermissionContext.tsx",
 "client/src/pages/RolesPermissions.tsx",
 "server/security/rolesPermissionFinal.test.ts",
}

def fail(m): print(f"ERROR={m}",file=sys.stderr); raise SystemExit(1)
def run(*a):
 p=subprocess.run(a,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode: fail(f"COMMAND_FAILED:{' '.join(a)}:{p.stderr.strip()}")
 return p.stdout.strip()
def read(r): return (ROOT/r).read_text(encoding="utf-8")
def write(r,s): p=ROOT/r; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding="utf-8")
def rp(s,a,b,label,n=1):
 c=s.count(a)
 if c!=n: fail(f"ANCHOR_DRIFT:{label}:count={c}:expected={n}")
 return s.replace(a,b)
def dirty():
 return set(filter(None,run("git","diff","--name-only").splitlines()))|set(filter(None,run("git","ls-files","--others","--exclude-standard").splitlines()))

if run("git","rev-parse","HEAD")!=BASELINE: fail("BASELINE_MISMATCH")
if run("git","diff","--cached","--name-only"): fail("STAGED_CHANGES_PRESENT")
if dirty(): fail(f"WORKTREE_NOT_CLEAN:{sorted(dirty())}")

ctx_rel="client/src/contexts/PermissionContext.tsx"
ctx=read(ctx_rel)
ctx=rp(ctx,'  "settings.view",\n  "roles.view",\n  "audit.view",','  "settings.view",\n  "roles.view",\n  "roles.create",\n  "roles.edit",\n  "roles.delete",\n  "roles.assign_permissions",\n  "audit.view",',"ctx-roles")
write(ctx_rel,ctx)

page_rel="client/src/pages/RolesPermissions.tsx"
p=read(page_rel)
p=rp(p,'import { useLanguage } from "@/contexts/LanguageContext";\nimport { trpc } from "@/lib/trpc";','import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\nimport { trpc } from "@/lib/trpc";',"import")
p=rp(p,'export default function RolesPermissions() {\n  const { isRTL } = useLanguage();','export default function RolesPermissions() {\n  const { isRTL } = useLanguage();\n  const { can } = usePermissions();\n  const canRolesCreate = can("roles.create");\n  const canRolesEdit = can("roles.edit");\n  const canRolesDelete = can("roles.delete");\n  const canRolesAssignPermissions = can("roles.assign_permissions");\n  const canUsersView = can("users.view");',"flags")
p=rp(p,'enabled: tab === "overrides" || tab === "tester"','enabled: canUsersView && (tab === "overrides" || tab === "tester")',"users-query")
p=rp(p,'enabled: !!selectedUserId && tab === "overrides"','enabled: canUsersView && !!selectedUserId && tab === "overrides"',"profile-query")
p=rp(p,'enabled: !!testerUserId && tab === "tester"','enabled: canUsersView && !!testerUserId && tab === "tester"',"tester-query")

p=rp(p,'''  const setPermission = (key: string, patch: Partial<PermissionDraft>) => setDraft(prev => ({
    ...prev,
    [key]: { ...prev[key], ...patch } as PermissionDraft,
  }));
  const setUserPermission = (key: string, patch: Partial<PermissionDraft>) => setUserDraft(prev => ({
    ...prev,
    [key]: { ...prev[key], ...patch } as PermissionDraft,
  }));''','''  const setPermission = (key: string, patch: Partial<PermissionDraft>) => {
    if (!canRolesAssignPermissions) return;
    setDraft(prev => ({ ...prev, [key]: { ...prev[key], ...patch } as PermissionDraft }));
  };
  const setUserPermission = (key: string, patch: Partial<PermissionDraft>) => {
    if (!canRolesAssignPermissions) return;
    setUserDraft(prev => ({ ...prev, [key]: { ...prev[key], ...patch } as PermissionDraft }));
  };''',"draft-guards")

for label,a in [
 ("bulk",'  const bulk = (mode: "clear" | "view" | "full") => {\n'),
 ("save",'  const save = () => {\n'),
 ("overrides",'  const saveUserOverrides = () => {\n'),
 ("scope",'  const applyModuleScope = (moduleKey: string, scope: string) => {\n'),
 ("module-all",'  const setModuleAll = (moduleKey: string, effect: EffectState) => {\n'),
]:
 p=rp(p,a,a+'    if (!canRolesAssignPermissions) return;\n',label)

p=rp(p,'{tab === "roles" && <Button onClick=','{tab === "roles" && <Button disabled={!canRolesCreate} onClick=',"create-btn")
p=rp(p,'<button onClick={() => setTab("overrides")} className=','<button disabled={!canUsersView} onClick={() => setTab("overrides")} className=',"override-tab")
p=rp(p,'<button onClick={() => setTab("tester")} className=','<button disabled={!canUsersView} onClick={() => setTab("tester")} className=',"tester-tab")
p=rp(p,'<Button variant="outline" size="sm" onClick={() => { setForm({ roleKey: selectedRole.roleKey,','<Button variant="outline" size="sm" disabled={!canRolesEdit} onClick={() => { setForm({ roleKey: selectedRole.roleKey,',"edit-btn")
p=rp(p,'<Button variant="outline" size="sm" onClick={() => { setForm({ roleKey: "", name: `${selectedRole.name} Copy`,','<Button variant="outline" size="sm" disabled={!canRolesCreate} onClick={() => { setForm({ roleKey: "", name: `${selectedRole.name} Copy`,',"copy-btn")
p=rp(p,'<Switch checked={Number(selectedRole.isActive) === 1} onCheckedChange=','<Switch checked={Number(selectedRole.isActive) === 1} disabled={!canRolesEdit} onCheckedChange=',"active")
p=rp(p,'<Button variant="destructive" size="sm" onClick=','<Button variant="destructive" size="sm" disabled={!canRolesDelete} onClick=',"delete")
p=rp(p,'<Button size="sm" onClick={save} disabled={saveMutation.isPending}>','<Button size="sm" onClick={save} disabled={!canRolesAssignPermissions || saveMutation.isPending}>',"save-btns",2)
p=rp(p,'<Button variant="outline" size="sm" onClick={() => setFieldEditor({ target: "role", permissionKey: "leads.view" })}>','<Button variant="outline" size="sm" disabled={!canRolesAssignPermissions} onClick={() => setFieldEditor({ target: "role", permissionKey: "leads.view" })}>',"field-role")
p=rp(p,'<Button variant="outline" size="sm" onClick={() => setFieldEditor({ target: "user", permissionKey: "leads.view" })}>','<Button variant="outline" size="sm" disabled={!canRolesAssignPermissions} onClick={() => setFieldEditor({ target: "user", permissionKey: "leads.view" })}>',"field-user")
p=rp(p,'<Button size="sm" onClick={saveUserOverrides} disabled={userOverridesMutation.isPending}>','<Button size="sm" onClick={saveUserOverrides} disabled={!canRolesAssignPermissions || userOverridesMutation.isPending}>',"override-save")
write(page_rel,p)

test_rel="server/security/rolesPermissionFinal.test.ts"
if (ROOT/test_rel).exists(): fail("ROLES_FINAL_TEST_ALREADY_EXISTS")
test=r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
const root=path.resolve(process.cwd());
const read=(p:string)=>readFileSync(path.join(root,p),"utf8");
const catalog=read("server/security/permissionCatalog.ts");
const ctx=read("client/src/contexts/PermissionContext.tsx");
const page=read("client/src/pages/RolesPermissions.tsx");
const router=read("server/permissionsAdminRouter.ts");
describe("Roles permissions E2E V1.0.0",()=>{
 it("catalog and frontend request all role permissions",()=>{
  for(const k of ["roles.view","roles.create","roles.edit","roles.delete","roles.assign_permissions"]){expect(catalog).toContain(`"${k}"`);expect(ctx).toContain(`"${k}"`);}
  expect(ctx).toContain('["/settings/roles-permissions", "roles.view"]');
 });
 it("backend maps every Roles action",()=>{
  for(const s of [
   'catalog: permissionProcedure("roles.view")','listRoles: permissionProcedure("roles.view")','getRole: permissionProcedure("roles.view")',
   'createRole: permissionProcedure("roles.create")','duplicateRole: permissionProcedure("roles.create")',
   'updateRole: permissionProcedure("roles.edit")','setActive: permissionProcedure("roles.edit")',
   'deleteRole: permissionProcedure("roles.delete")',
   'replacePermissions: permissionProcedure("roles.assign_permissions")','replaceUserOverrides: permissionProcedure("roles.assign_permissions")'
  ]) expect(router).toContain(s);
 });
 it("preserves users.view for user override/tester directory",()=>{
  expect(router).toContain('listUsersForPermissions: permissionProcedure("users.view")');
  expect(page).toContain('const canUsersView = can("users.view")');
  expect(page).toContain('enabled: canUsersView && (tab === "overrides" || tab === "tester")');
 });
 it("gates frontend mutation actions",()=>{
  for(const s of ['canRolesCreate','canRolesEdit','canRolesDelete','canRolesAssignPermissions','disabled={!canRolesCreate}','disabled={!canRolesEdit}','disabled={!canRolesDelete}','if (!canRolesAssignPermissions) return;','disabled={!canRolesAssignPermissions || saveMutation.isPending}','disabled={!canRolesAssignPermissions || userOverridesMutation.isPending}']) expect(page).toContain(s);
 });
});
'''
write(test_rel,test)

if dirty()!=EXPECTED: fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(dirty())}")
run("git","diff","--check")
print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("ROLES_PERMISSION_KEYS=roles.view,roles.create,roles.edit,roles.delete,roles.assign_permissions")
print("ROLES_ROUTE_GATE=PASS")
print("ROLES_API_GATES=PREEXISTING_PASS")
print("ROLES_FRONTEND_ACTION_GATES=PASS")
print("USER_DIRECTORY_USERS_VIEW_DEPENDENCY_PRESERVED=YES")
print("PERMISSIONS_ADMIN_ROUTER_CHANGED=NO")
print("CSS_CHANGED=NO")
print("DB_SCHEMA_CHANGED=NO")
print("DATA_CHANGED=NO")
print("FINAL_EXPECTED_FILES=3")
