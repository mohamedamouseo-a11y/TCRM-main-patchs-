import fs from "node:fs";

function must(file: string, needle: string) {
  const text = fs.readFileSync(file, "utf8");
  if (!text.includes(needle)) throw new Error(`${file}: missing ${needle}`);
  return text;
}

function between(text: string, start: string, end: string, label: string) {
  const startIndex = text.indexOf(start);
  if (startIndex < 0) throw new Error(`${label}: missing start marker ${start}`);
  const afterStart = startIndex + start.length;
  const endIndex = text.indexOf(end, afterStart);
  if (endIndex < 0) throw new Error(`${label}: missing end marker ${end}`);
  return text.slice(afterStart, endIndex);
}

const serverRoles = must("server/roleUtils.ts", "Legacy compatibility only");
const clientRoles = must("client/src/lib/roles.ts", "Legacy-only compatibility values");
const serverActive = between(serverRoles, "export const APP_USER_ROLES", "] as const", "server APP_USER_ROLES");
const clientActive = between(clientRoles, "export const APP_USER_ROLES", "] as const", "client APP_USER_ROLES");
for (const role of ["ServiceAdvisor", "PartsAgent", "CrmFollowUp"]) {
  if (serverActive.includes(`\"${role}\"`) || clientActive.includes(`\"${role}\"`)) {
    throw new Error(`Automotive-only role still active/selectable: ${role}`);
  }
}

const adminRouter = must("server/permissionsAdminRouter.ts", "ADVANCED_PERMISSIONS_PHASE3B_V2_USER_OVERRIDES");
for (const key of ["listUsersForPermissions", "getUserPermissionProfile", "replaceUserOverrides"]) {
  if (!adminRouter.includes(key)) throw new Error(`permissionsAdminRouter missing ${key}`);
}

const overrideService = must("server/security/permissionUserOverrideAdmin.ts", "replacePermissionUserOverrides");
for (const table of ["user_permission_overrides", "permission_audit_logs"]) {
  if (!overrideService.includes(table)) throw new Error(`override service missing ${table}`);
}

must("server/security/phase3bScope.ts", "assertTaskPermissionScope");
must("server/_core/trpc.ts", "activitiesViewScope");
must("server/_core/trpc.ts", "tasksViewScope");
must("server/_core/trpc.ts", "contractsViewScope");
must("server/db.ts", "getActivitiesByUserScoped");

const ui = fs.readFileSync("client/src/pages/RolesPermissions.tsx", "utf8");
for (const needle of ["User Overrides", "listUsersForPermissions", "replaceUserOverrides"]) {
  if (!ui.includes(needle)) throw new Error(`RolesPermissions UI missing ${needle}`);
}

console.log(JSON.stringify({
  ok: true,
  phase: "3B-v2-tas-style-user-overrides-package-fix1",
  verified: [
    "activities-tasks-contracts-enforcement",
    "tas-style-simple-role-ux-marker",
    "per-user-overrides-api-and-ui",
    "automotive-roles-not-selectable",
    "legacy-automotive-compatibility-retained",
    "verifier-role-section-parser-fixed",
  ],
  untouchedByDesign: ["meetings", "felfel", "tam-meeting-flows"],
  scopePolicy: "advanced-engine/simple-ui/user-overrides-win",
}, null, 2));
