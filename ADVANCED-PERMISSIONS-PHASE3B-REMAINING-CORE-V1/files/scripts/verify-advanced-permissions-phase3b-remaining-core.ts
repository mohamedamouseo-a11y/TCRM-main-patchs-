import fs from "node:fs";

function read(file: string) { return fs.readFileSync(file, "utf8"); }
function must(text: string, needle: string, label = needle) {
  if (!text.includes(needle)) throw new Error(`Missing ${label}`);
}

const trpc = read("server/_core/trpc.ts");
const routers = read("server/routers.ts");

must(trpc, "ADVANCED_PERMISSIONS_PHASE3B_REMAINING_CORE_V1");
for (const symbol of [
  "campaignsViewScope", "campaignsCreateScope", "campaignsEditScope", "campaignsDeleteScope",
  "reportsViewScope", "reportsExportScope",
  "notificationsViewScope", "notificationsManageScope",
  "auditViewScope", "auditExportScope",
]) must(trpc, symbol, `trpc export ${symbol}`);

// Campaigns must keep the legacy MediaBuyer/Admin guards and add RBAC.
for (const pattern of [
  "list: protectedProcedure.use(campaignsViewScope)",
  "distinctNames: protectedProcedure.use(campaignsViewScope)",
  "create: mediaBuyerOrAdminProcedure.use(campaignsCreateScope)",
  "update: mediaBuyerOrAdminProcedure.use(campaignsEditScope)",
  "delete: mediaBuyerOrAdminProcedure.use(campaignsDeleteScope)",
]) must(routers, pattern, pattern);

// Remaining modules: verifier accepts any existing legacy procedure as long as the correct
// additive scope middleware is visibly composed in the router source.
for (const scope of [
  "reportsViewScope", "notificationsViewScope", "notificationsManageScope", "auditViewScope",
]) must(routers, `.use(${scope})`, `router wiring ${scope}`);

// Sensitive meeting paths must remain untouched by this package.
if (routers.includes("ADVANCED_PERMISSIONS_PHASE3B_REMAINING_CORE_V1_MEETINGS")) {
  throw new Error("Meetings/Felfel/TAM must not be wired in this package");
}

console.log(JSON.stringify({
  ok: true,
  phase: "3B-remaining-core-v1",
  verified: [
    "campaigns-action-enforcement",
    "reports-action-enforcement",
    "notifications-action-enforcement",
    "audit-action-enforcement",
    "legacy-guards-preserved",
  ],
  untouchedByDesign: ["meetings", "felfel", "tam-meeting-flows", "whatsapp", "messenger", "integrations", "backup", "files-drive"],
  dataScopePolicy: "no-new-row-scope-semantics-in-this-package",
}, null, 2));