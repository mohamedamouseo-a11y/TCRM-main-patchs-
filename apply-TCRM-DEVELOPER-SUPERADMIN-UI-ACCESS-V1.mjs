import fs from "node:fs";
import { execFileSync } from "node:child_process";

const BASE_SHA = "9a7842c90667706a4bf37802f9373fce5fa6b202";
const PATCH_MARKER = "TCRM_DEVELOPER_SUPERADMIN_UI_ACCESS_V1";

function fail(message, code = 2) {
  console.error(message);
  process.exit(code);
}

function read(path) {
  return fs.readFileSync(path, "utf8");
}

function replaceOnce(source, before, after, label) {
  if (source.includes(after)) return source;
  const first = source.indexOf(before);
  if (first === -1) fail(`PATCH_TARGET_NOT_FOUND: ${label}`);
  if (source.indexOf(before, first + before.length) !== -1) {
    fail(`PATCH_TARGET_AMBIGUOUS: ${label}`);
  }
  return source.slice(0, first) + after + source.slice(first + before.length);
}

function insertBeforeOnce(source, anchor, addition, label) {
  if (source.includes(addition.trim())) return source;
  const first = source.indexOf(anchor);
  if (first === -1) fail(`PATCH_TARGET_NOT_FOUND: ${label}`);
  if (source.indexOf(anchor, first + anchor.length) !== -1) {
    fail(`PATCH_TARGET_AMBIGUOUS: ${label}`);
  }
  return source.slice(0, first) + addition + source.slice(first);
}

let head = "";
try {
  head = execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();
} catch {
  fail("PATCH_PRECHECK_FAILED: unable to read git HEAD");
}
if (head !== BASE_SHA) {
  fail(`PATCH_BASE_MISMATCH: expected ${BASE_SHA}, got ${head}`);
}

const paths = {
  roles: "client/src/lib/roles.ts",
  layout: "client/src/components/CRMLayout.tsx",
  dashboard: "client/src/pages/AgentDashboard.tsx",
  settings: "client/src/pages/AdminSettings.tsx",
  trpc: "server/_core/trpc.ts",
  developerHub: "server/routes/developerHub.ts",
};

const original = Object.fromEntries(Object.entries(paths).map(([key, path]) => [key, read(path)]));
const next = { ...original };

// 1) Client-side access-role helper: Developer keeps its real role identity,
//    but UI permission checks can deliberately treat it as Admin.
next.roles = insertBeforeOnce(
  next.roles,
  "export function isAdminRole(role?: string | null): boolean {",
  `// ${PATCH_MARKER}\nexport function normalizeAccessRole(role?: string | null): string {\n  const normalized = normalizeUserRole(role);\n  return normalized === DEVELOPER_ROLE ? "Admin" : normalized;\n}\n\n`,
  "roles.normalizeAccessRole",
);

// 2) Sidebar/navigation: Developer receives the same UI navigation surface as Admin.
next.layout = replaceOnce(
  next.layout,
  'import { isTaraModeratorRole, normalizeUserRole } from "@/lib/roles";',
  'import { isTaraModeratorRole, normalizeAccessRole, normalizeUserRole } from "@/lib/roles";',
  "CRMLayout roles import",
);
next.layout = replaceOnce(
  next.layout,
  '  const slaRole = normalizeUserRole(user?.role ?? "");',
  '  const slaRole = normalizeAccessRole(user?.role ?? "");',
  "CRMLayout SLA access role",
);
next.layout = replaceOnce(
  next.layout,
  "  const role = actualRole;",
  "  const role = normalizeAccessRole(actualRole);",
  "CRMLayout navigation access role",
);

// 3) Default dashboard: Developer sees the Admin dashboard shell/data path.
next.dashboard = replaceOnce(
  next.dashboard,
  'import { normalizeUserRole } from "@/lib/roles";',
  'import { normalizeAccessRole, normalizeUserRole } from "@/lib/roles";',
  "AgentDashboard roles import",
);
next.dashboard = replaceOnce(
  next.dashboard,
  '  const userRole = user?.role ? normalizeUserRole(user.role) : "";',
  '  const actualUserRole = user?.role ? normalizeUserRole(user.role) : "";\n  const userRole = normalizeAccessRole(actualUserRole);',
  "AgentDashboard Developer admin-like access",
);

// 4) Settings UI: Developer sees the same settings catalog as Super Admin.
//    Server-side Developer protections remain authoritative for forbidden actions.
next.settings = replaceOnce(
  next.settings,
  'import { APP_USER_ROLES, isAdminRole, isMediaBuyerRole } from "@/lib/roles";',
  'import { APP_USER_ROLES, isAdminRole, isMediaBuyerRole, normalizeUserRole } from "@/lib/roles";',
  "AdminSettings roles import",
);
next.settings = replaceOnce(
  next.settings,
  '  const isSuperAdmin = (user?.email === "admin@tamiyouz.com" || user?.email === "superadmin@tamiyouzalrowad.com") && isMainCRM;',
  '  const isDeveloper = normalizeUserRole(user?.role ?? "") === "Developer";\n  const isSuperAdmin = ((user?.email === "admin@tamiyouz.com" || user?.email === "superadmin@tamiyouzalrowad.com") || isDeveloper) && isMainCRM;',
  "AdminSettings Developer SuperAdmin UI visibility",
);

// 5) Central tRPC authorization: Developer is admin-like for access, while
//    developerAccessProtection and developerDataProtection still block unsafe
//    mutations and sanitize returned production data.
next.trpc = replaceOnce(
  next.trpc,
  '  return normalized === "admin" || normalized === "superadmin" || normalized === "super_admin";',
  '  return normalized === "admin" || normalized === "superadmin" || normalized === "super_admin" || isDeveloperRole(role);',
  "tRPC adminProcedure Developer access",
);

// 6) Developer Hub: allow Developer role through the Hub gate without granting
//    Super Admin identity. Keep direct secrets redacted for Developer sessions.
next.developerHub = replaceOnce(
  next.developerHub,
  'import { authenticateRequest } from "../auth";',
  'import { authenticateRequest } from "../auth";\nimport { isDeveloperRole } from "../roleUtils";',
  "Developer Hub role import",
);

if (!next.developerHub.includes("requireDeveloperHubAccess")) {
  if (!next.developerHub.includes("requireSuperAdmin")) {
    fail("PATCH_TARGET_NOT_FOUND: Developer Hub authorization function");
  }
  next.developerHub = next.developerHub.replaceAll("requireSuperAdmin", "requireDeveloperHubAccess");
}

next.developerHub = replaceOnce(
  next.developerHub,
  `  const SUPER_ADMIN_EMAILS = ["admin@tamiyouz.com", "superadmin@tamiyouzalrowad.com"];\n  if (!SUPER_ADMIN_EMAILS.includes(user.email ?? "")) {\n    res.status(403).json({ error: "Super Admin access required" });\n    return null;\n  }`,
  `  const SUPER_ADMIN_EMAILS = ["admin@tamiyouz.com", "superadmin@tamiyouzalrowad.com"];\n  const developerAccess = isDeveloperRole((user as any).role);\n  if (!SUPER_ADMIN_EMAILS.includes(user.email ?? "") && !developerAccess) {\n    res.status(403).json({ error: "Developer Hub access required" });\n    return null;\n  }`,
  "Developer Hub role authorization",
);

next.developerHub = replaceOnce(
  next.developerHub,
  `developerHubRouter.get("/developer-hub/status", async (req, res) => {\n  const user = await requireDeveloperHubAccess(req, res);\n  if (!user) return;\n  let state = await ensureState();`,
  `developerHubRouter.get("/developer-hub/status", async (req, res) => {\n  const user = await requireDeveloperHubAccess(req, res);\n  if (!user) return;\n  const developerMode = isDeveloperRole((user as any).role);\n  let state = await ensureState();`,
  "Developer Hub status developer mode",
);

next.developerHub = replaceOnce(
  next.developerHub,
  `    webhookSecret: state.webhookSecret,\n    aiAccessUrl: \`${'${baseUrl}'}/api/ai/context/latest?token=${'${state.aiAccessToken}'}\`,\n    aiAccessTokenMasked: \`${'${state.aiAccessToken.slice(0, 6)}'}••••${'${state.aiAccessToken.slice(-4)}'}\`,`,
  `    webhookSecret: developerMode ? "[REDACTED]" : state.webhookSecret,\n    aiAccessUrl: developerMode ? "" : \`${'${baseUrl}'}/api/ai/context/latest?token=${'${state.aiAccessToken}'}\`,\n    aiAccessTokenMasked: developerMode ? "[REDACTED]" : \`${'${state.aiAccessToken.slice(0, 6)}'}••••${'${state.aiAccessToken.slice(-4)}'}\`,`,
  "Developer Hub secret redaction",
);

const changed = Object.keys(paths).filter((key) => next[key] !== original[key]);
if (changed.length === 0) {
  console.log("PATCH_ALREADY_APPLIED");
  process.exit(0);
}

// Validate all target transformations before writing anything.
if (!next.roles.includes("normalizeAccessRole")) fail("PATCH_VALIDATION_FAILED: roles helper");
if (!next.layout.includes("const role = normalizeAccessRole(actualRole);")) fail("PATCH_VALIDATION_FAILED: CRMLayout");
if (!next.dashboard.includes("const userRole = normalizeAccessRole(actualUserRole);")) fail("PATCH_VALIDATION_FAILED: AgentDashboard");
if (!next.settings.includes('const isDeveloper = normalizeUserRole(user?.role ?? "") === "Developer";')) fail("PATCH_VALIDATION_FAILED: AdminSettings");
if (!next.trpc.includes("isDeveloperRole(role);")) fail("PATCH_VALIDATION_FAILED: adminProcedure");
if (!next.developerHub.includes("requireDeveloperHubAccess")) fail("PATCH_VALIDATION_FAILED: Developer Hub gate");
if (!next.developerHub.includes('webhookSecret: developerMode ? "[REDACTED]"')) fail("PATCH_VALIDATION_FAILED: Developer Hub secret redaction");

for (const [key, path] of Object.entries(paths)) {
  if (next[key] !== original[key]) fs.writeFileSync(path, next[key], "utf8");
}

console.log("PATCH_APPLIED");
console.log(`BASE_SHA=${BASE_SHA}`);
for (const key of changed) console.log(paths[key]);
