import fs from "node:fs";
import { execFileSync } from "node:child_process";

const BASE_SHA = "15d30388f079cad3aeaa80bd7cf67e8847e320c5";
const PATCH_ID = "TCRM_DEVELOPER_MARKETING_ZERO_DATA_V1";

const files = {
  tiktok: "client/src/pages/TikTokCampaignsPage.tsx",
  google: "client/src/pages/GoogleAdsCampaignsPage.tsx",
  snapchat: "client/src/pages/SnapchatCampaignsPage.tsx",
  linkedin: "client/src/pages/LinkedInCampaignsPage.tsx",
  sanitizer: "server/utils/developerDataSanitizer.ts",
  accessPolicy: "server/utils/developerAccessPolicy.ts",
  trpc: "server/_core/trpc.ts",
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

for (const key of ["tiktok", "google", "snapchat", "linkedin"]) {
  next[key] = replaceOnce(
    next[key],
    'import { useAuth } from "@/_core/hooks/useAuth";',
    'import { useAuth } from "@/_core/hooks/useAuth";\nimport { isAdminRole, isMediaBuyerRole } from "@/lib/roles";',
    `${key}.roles import`,
  );

  next[key] = replaceOnce(
    next[key],
    `  const role = user?.role ?? "";\n  const hasAccess = ["Admin", "admin", "MediaBuyer"].includes(role);`,
    `  const role = user?.role ?? "";\n  const hasAccess = isAdminRole(role) || isMediaBuyerRole(role); // ${PATCH_ID}`,
    `${key}.Developer page access`,
  );
}

next.sanitizer = insertBeforeOnce(
  next.sanitizer,
  `/**\n * Returns a deep sanitized copy of the value with customer/PII/financial data zeroed.\n * The source object is never mutated.\n */`,
  `// ${PATCH_ID}\nfunction sanitizeDeveloperMarketingValue(value: unknown): unknown {\n  if (value === null || value === undefined) return value;\n  if (Array.isArray(value)) return [];\n  if (value instanceof Date) return new Date(0);\n  if (typeof value === "number" || typeof value === "bigint") return 0;\n  if (typeof value === "string") return "0";\n  if (typeof value === "boolean") return false;\n  if (typeof value !== "object") return null;\n\n  const result: Record<string, unknown> = {};\n  for (const [key, child] of Object.entries(value as Record<string, unknown>)) {\n    result[key] = sanitizeDeveloperMarketingValue(child);\n  }\n  return result;\n}\n\nexport function sanitizeDeveloperMarketingData(value: unknown): unknown {\n  return sanitizeDeveloperMarketingValue(value);\n}\n\n`,
  "developer marketing sanitizer",
);

next.accessPolicy = insertBeforeOnce(
  next.accessPolicy,
  `const BLOCKED_USER_UPDATE_FIELDS = new Set([`,
  `const DEVELOPER_PRODUCTION_AD_MUTATION_PREFIXES = [\n  "meta.",\n  "metaCombined.",\n  "tiktok.",\n  "googleAds.",\n  "snapchat.",\n  "linkedin.",\n] as const;\n\nfunction isDeveloperProductionAdMutation(path: string): boolean {\n  return DEVELOPER_PRODUCTION_AD_MUTATION_PREFIXES.some((prefix) => path.startsWith(prefix));\n}\n\n`,
  "developer ad mutation prefixes",
);

next.accessPolicy = replaceOnce(
  next.accessPolicy,
  `  if (isExportMutationPath(path)) {\n    return "Developer mode cannot export production data.";\n  }\n\n  return null;`,
  `  if (isExportMutationPath(path)) {\n    return "Developer mode cannot export production data.";\n  }\n\n  if (isDeveloperProductionAdMutation(path)) {\n    return "Developer mode cannot modify live advertising platforms or campaign data.";\n  }\n\n  return null;`,
  "developer ad mutation denial",
);

next.trpc = replaceOnce(
  next.trpc,
  `import { sanitizeDeveloperData } from "../utils/developerDataSanitizer";`,
  `import { sanitizeDeveloperData, sanitizeDeveloperMarketingData } from "../utils/developerDataSanitizer";`,
  "trpc marketing sanitizer import",
);

next.trpc = insertBeforeOnce(
  next.trpc,
  `const developerDataProtection = t.middleware(async (opts) => {`,
  `const DEVELOPER_MARKETING_ZERO_DATA_PREFIXES = [\n  "meta.",\n  "metaCombined.",\n  "tiktok.",\n  "googleAds.",\n  "snapchat.",\n  "linkedin.",\n] as const;\n\nfunction isDeveloperMarketingZeroDataPath(path: string): boolean {\n  return DEVELOPER_MARKETING_ZERO_DATA_PREFIXES.some((prefix) => path.startsWith(prefix));\n}\n\n// ${PATCH_ID}\n`,
  "trpc marketing path matcher",
);

next.trpc = replaceOnce(
  next.trpc,
  `  return {\n    ...result,\n    data: sanitizeDeveloperData(result.data),\n  } as typeof result;`,
  `  return {\n    ...result,\n    data: isDeveloperMarketingZeroDataPath(opts.path)\n      ? sanitizeDeveloperMarketingData(result.data)\n      : sanitizeDeveloperData(result.data),\n  } as typeof result;`,
  "trpc path-aware developer sanitizer",
);

for (const key of ["tiktok", "google", "snapchat", "linkedin"]) {
  if (!next[key].includes("isAdminRole(role) || isMediaBuyerRole(role)")) {
    fail(`PATCH_VALIDATION_FAILED: ${key} Developer access`);
  }
}

if (!next.sanitizer.includes("sanitizeDeveloperMarketingData")) {
  fail("PATCH_VALIDATION_FAILED: marketing sanitizer missing");
}
if (!next.trpc.includes("isDeveloperMarketingZeroDataPath(opts.path)")) {
  fail("PATCH_VALIDATION_FAILED: marketing sanitizer not wired into tRPC");
}
if (!next.accessPolicy.includes("isDeveloperProductionAdMutation(path)")) {
  fail("PATCH_VALIDATION_FAILED: marketing mutation block missing");
}
if (!next.trpc.includes("developerAccessProtection")) {
  fail("PATCH_SAFETY_FAILED: developerAccessProtection missing");
}
if (!next.trpc.includes("developerDataProtection")) {
  fail("PATCH_SAFETY_FAILED: developerDataProtection missing");
}
if (!next.accessPolicy.includes('"users.delete"')) {
  fail("PATCH_SAFETY_FAILED: existing Developer access policy unexpectedly changed");
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
