import fs from "node:fs";
import { execFileSync } from "node:child_process";

const BASE_SHA = "0fdb4ecaeb252a427143b22eb4dcb082a5647d69";
const PATCH_ID = "TCRM_DEVELOPER_FULL_SURFACE_ZERO_DATA_V1";

const files = {
  team: "client/src/pages/TeamDashboard.tsx",
  trashPage: "client/src/pages/TrashPage.tsx",
  auditPage: "client/src/pages/AuditLogPage.tsx",
  sanitizer: "server/utils/developerDataSanitizer.ts",
  accessPolicy: "server/utils/developerAccessPolicy.ts",
  trpc: "server/_core/trpc.ts",
  bdIndex: "server/routes/bd/index.ts",
};

function fail(message, code = 2) {
  console.error(message);
  process.exit(code);
}

function read(path) {
  if (!fs.existsSync(path)) fail(`PATCH_FILE_MISSING: ${path}`);
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

const original = Object.fromEntries(
  Object.entries(files).map(([key, path]) => [key, read(path)]),
);
const next = { ...original };

if (Object.values(original).some((source) => source.includes(PATCH_ID))) {
  console.log("PATCH_ALREADY_APPLIED");
  process.exit(0);
}

// UI page guards: Developer is Admin-like for VIEWING only.
// Actual role remains Developer so server-side zero-data / mutation policy stays active.
next.team = replaceOnce(
  next.team,
  'import { useAuth } from "@/_core/hooks/useAuth";',
  'import { useAuth } from "@/_core/hooks/useAuth";\nimport { isAdminRole } from "@/lib/roles";',
  "TeamDashboard roles import",
);

next.team = replaceOnce(
  next.team,
  `  if (!["Admin", "SalesManager", "admin"].includes(user?.role ?? "")) {`,
  `  if (!isAdminRole(user?.role) && user?.role !== "SalesManager") { // ${PATCH_ID}`,
  "TeamDashboard Developer access",
);

next.trashPage = replaceOnce(
  next.trashPage,
  'import { useAuth } from "@/_core/hooks/useAuth";',
  'import { useAuth } from "@/_core/hooks/useAuth";\nimport { isAdminRole } from "@/lib/roles";',
  "TrashPage roles import",
);

next.trashPage = replaceOnce(
  next.trashPage,
  `  if (normalizedRole !== "admin" && normalizedRole !== "superadmin") {`,
  `  if (!isAdminRole(user?.role)) { // ${PATCH_ID}`,
  "TrashPage Developer access",
);

next.auditPage = replaceOnce(
  next.auditPage,
  'import { useAuth } from "@/_core/hooks/useAuth";',
  'import { useAuth } from "@/_core/hooks/useAuth";\nimport { isAdminRole } from "@/lib/roles";',
  "AuditLogPage roles import",
);

next.auditPage = replaceOnce(
  next.auditPage,
  `  if (role !== "Admin" && role !== "admin") {`,
  `  if (!isAdminRole(role)) { // ${PATCH_ID}`,
  "AuditLogPage Developer access",
);

// Strict Developer zero-data helper. Reuse the already-tested deep zero implementation used by Marketing.
next.sanitizer = replaceOnce(
  next.sanitizer,
  `export function sanitizeDeveloperMarketingData(value: unknown): unknown {
  return sanitizeDeveloperMarketingValue(value);
}

/**`,
  `export function sanitizeDeveloperMarketingData(value: unknown): unknown {
  return sanitizeDeveloperMarketingValue(value);
}

// ${PATCH_ID}
export function sanitizeDeveloperStrictZeroData(value: unknown): unknown {
  return sanitizeDeveloperMarketingValue(value);
}

/**`,
  "strict Developer zero-data export",
);

// tRPC strict zero-data surfaces.
next.trpc = replaceOnce(
  next.trpc,
  `import { sanitizeDeveloperData, sanitizeDeveloperMarketingData } from "../utils/developerDataSanitizer";`,
  `import { sanitizeDeveloperData, sanitizeDeveloperMarketingData, sanitizeDeveloperStrictZeroData } from "../utils/developerDataSanitizer";`,
  "tRPC strict zero-data import",
);

next.trpc = insertBeforeOnce(
  next.trpc,
  `// TCRM_DEVELOPER_MARKETING_ZERO_DATA_V1
const developerDataProtection = t.middleware(async (opts) => {`,
  `const DEVELOPER_STRICT_ZERO_DATA_PREFIXES = [
  "dashboard.",
  "trash.",
  "auditLogs.",
  "users.",
] as const;

function isDeveloperStrictZeroDataPath(path: string): boolean {
  return DEVELOPER_STRICT_ZERO_DATA_PREFIXES.some((prefix) => path.startsWith(prefix));
}

// ${PATCH_ID}
`,
  "tRPC strict zero-data matcher",
);

next.trpc = replaceOnce(
  next.trpc,
  `    data: isDeveloperMarketingZeroDataPath(opts.path)
      ? sanitizeDeveloperMarketingData(result.data)
      : sanitizeDeveloperData(result.data),`,
  `    data: isDeveloperMarketingZeroDataPath(opts.path)
      ? sanitizeDeveloperMarketingData(result.data)
      : isDeveloperStrictZeroDataPath(opts.path)
        ? sanitizeDeveloperStrictZeroData(result.data)
        : sanitizeDeveloperData(result.data),`,
  "tRPC path-aware strict zero-data",
);

// Mutation protection for destructive / production admin surfaces.
next.accessPolicy = replaceOnce(
  next.accessPolicy,
  `  "crmFiles.createPublicViewOnlyShareLink": "Developer mode cannot create public CRM file links.",
};`,
  `  "crmFiles.createPublicViewOnlyShareLink": "Developer mode cannot create public CRM file links.",
  "trash.restore": "Developer mode cannot restore production records from Trash.",
  "trash.permanentDelete": "Developer mode cannot permanently delete production records.",
  "auditLogs.undo": "Developer mode cannot undo production audit operations.",
};`,
  "Developer destructive mutation denials",
);

// Business Development is Express, not tRPC.
// Developer gets bd_admin VIEW access, all non-read requests are blocked,
// and GET responses are strict zero-data except /me permission shape.
next.bdIndex = replaceOnce(
  next.bdIndex,
  `import { and, eq } from "drizzle-orm";`,
  `import { and, eq } from "drizzle-orm";
import { isDeveloperRole } from "../../roleUtils";
import { sanitizeDeveloperStrictZeroData } from "../../utils/developerDataSanitizer";`,
  "BD Developer imports",
);

next.bdIndex = replaceOnce(
  next.bdIndex,
  `    // Admin/SalesManager auto-granted; others require explicit row
    const isAuto = user.role === "Admin" || user.role === "SalesManager" || user.role === "Moderator";
    const bdRole = access[0]?.role ?? (isAuto ? "bd_admin" : null);
    if (!bdRole) return res.status(403).json({ error: "bd_access_required" });

    req.bdUser = {
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
      bdRole,
    };
    next();`,
  `    // Admin/SalesManager/Developer auto-granted for the BD UI; others require explicit row.
    const isDeveloper = isDeveloperRole(user.role);
    const isAuto = user.role === "Admin" || user.role === "SalesManager" || user.role === "Moderator" || isDeveloper;
    const bdRole = access[0]?.role ?? (isAuto ? "bd_admin" : null);
    if (!bdRole) return res.status(403).json({ error: "bd_access_required" });

    if (isDeveloper && !["GET", "HEAD", "OPTIONS"].includes(req.method.toUpperCase())) {
      return res.status(403).json({ error: "developer_production_mutation_blocked" });
    }

    req.bdUser = {
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
      bdRole,
    };

    if (isDeveloper) {
      const originalJson = res.json.bind(res);
      res.json = ((body: any) => {
        const isMeRoute = req.path === "/me" || req.path.endsWith("/me");
        if (isMeRoute && body && typeof body === "object" && "user" in body) {
          return originalJson({
            user: {
              id: 0,
              name: "0",
              email: "0@0.local",
              role: "Developer",
              bdRole: "bd_admin",
            },
          });
        }
        return originalJson(sanitizeDeveloperStrictZeroData(body));
      }) as typeof res.json;
    }

    // ${PATCH_ID}
    next();`,
  "BD Developer view-only zero-data access",
);

// Safety invariants.
if (!next.team.includes("if (!isAdminRole(user?.role) && user?.role !== \"SalesManager\")")) {
  fail("PATCH_VALIDATION_FAILED: Team Dashboard Developer access missing");
}
if (!next.trashPage.includes("if (!isAdminRole(user?.role))")) {
  fail("PATCH_VALIDATION_FAILED: Trash Developer access missing");
}
if (!next.auditPage.includes("if (!isAdminRole(role))")) {
  fail("PATCH_VALIDATION_FAILED: Audit Log Developer access missing");
}
if (!next.trpc.includes('"dashboard."') || !next.trpc.includes('"trash."') || !next.trpc.includes('"auditLogs."') || !next.trpc.includes('"users."')) {
  fail("PATCH_VALIDATION_FAILED: strict zero-data tRPC paths incomplete");
}
if (!next.trpc.includes("developerAccessProtection") || !next.trpc.includes("developerDataProtection")) {
  fail("PATCH_SAFETY_FAILED: Developer middleware missing");
}
if (!next.accessPolicy.includes('"users.delete"') || !next.accessPolicy.includes('"auth.adminSetPassword"')) {
  fail("PATCH_SAFETY_FAILED: existing user-security restrictions missing");
}
if (!next.accessPolicy.includes('"trash.permanentDelete"') || !next.accessPolicy.includes('"auditLogs.undo"')) {
  fail("PATCH_SAFETY_FAILED: destructive surface mutation blocks missing");
}
if (!next.bdIndex.includes("developer_production_mutation_blocked")) {
  fail("PATCH_VALIDATION_FAILED: BD Developer mutation block missing");
}
if (!next.bdIndex.includes("sanitizeDeveloperStrictZeroData(body)")) {
  fail("PATCH_VALIDATION_FAILED: BD strict zero-data response wrapper missing");
}
if (!next.bdIndex.includes('role: "Developer"') || !next.bdIndex.includes('bdRole: "bd_admin"')) {
  fail("PATCH_VALIDATION_FAILED: BD /me Developer UI capability shape missing");
}

// Existing Marketing zero-data must remain.
if (!next.trpc.includes("isDeveloperMarketingZeroDataPath(opts.path)")) {
  fail("PATCH_SAFETY_FAILED: Marketing zero-data route protection missing");
}
if (!next.accessPolicy.includes("isDeveloperProductionAdMutation(path)")) {
  fail("PATCH_SAFETY_FAILED: Marketing mutation protection missing");
}

const changed = Object.keys(files).filter((key) => next[key] !== original[key]);
if (changed.length === 0) {
  console.log("PATCH_ALREADY_APPLIED");
  process.exit(0);
}

for (const [key, path] of Object.entries(files)) {
  if (next[key] !== original[key]) {
    fs.writeFileSync(path, next[key], "utf8");
  }
}

console.log("PATCH_APPLIED");
console.log(`PATCH_ID=${PATCH_ID}`);
console.log(`BASE_SHA=${BASE_SHA}`);
for (const key of changed) console.log(files[key]);
