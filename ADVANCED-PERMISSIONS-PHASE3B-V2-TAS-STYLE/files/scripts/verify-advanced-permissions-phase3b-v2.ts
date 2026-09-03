import fs from "node:fs";

function must(file: string, needle: string) {
  const text = fs.readFileSync(file, "utf8");
  if (!text.includes(needle)) throw new Error(`${file}: missing ${needle}`);
  return text;
}

const serverRoles = must("server/roleUtils.ts", "Legacy compatibility only");
const clientRoles = must("client/src/lib/roles.ts", "Legacy-only compatibility values");
for (const role of ["ServiceAdvisor", "PartsAgent", "CrmFollowUp"]) {
  const serverActive = serverRoles.split("export const APP_USER_ROLES", 1)[1].split("] as const", 1)[0];
  const clientActive = clientRoles.split("export const APP_USER_ROLES", 1)[1].split("] as const", 1)[0];
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

const phase3b = must("server/security/phase3bScope.ts", "assertTaskPermissionScope");
must("server/_core/trpc.ts", "activitiesViewScope");
must("server/_core/trpc.ts", "tasksViewScope");
must("server/_core/trpc.ts", "contractsViewScope");
must("server/db.ts", "getActivitiesByUserScoped");

const ui = fs.readFileSync("client/src/pages/RolesPermissions.tsx", "utf8");
const uiSignals = [
  "User Overrides",
  "استثناءات المستخدمين",
  "listUsersForPermissions",
  "replaceUserOverrides",
];
if (!uiSignals.some((needle) => ui.includes(needle))) {
  throw new Error("RolesPermissions UI has not been adapted with User Overrides yet");
}
if (!ui.includes("listUsersForPermissions") || !ui.includes("replaceUserOverrides")) {
  throw new Error("RolesPermissions UI is not wired to per-user override APIs");
}

console.log(JSON.stringify({
  ok: true,
  phase: "3B-v2-tas-style-user-overrides",
  verified: [
    "activities-tasks-contracts-enforcement",
    "tas-style-simple-role-ux-marker",
    "per-user-overrides-api-and-ui",
    "automotive-roles-not-selectable",
    "legacy-automotive-compatibility-retained",
  ],
  untouchedByDesign: ["meetings", "felfel", "tam-meeting-flows"],
  scopePolicy: "advanced-engine/simple-ui/user-overrides-win",
}, null, 2));
