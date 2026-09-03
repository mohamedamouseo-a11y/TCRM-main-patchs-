// TCRM Advanced Permissions — Phase 3A Reviewed Fix V1 verification.
import fs from "node:fs";
import path from "node:path";
import { sql } from "drizzle-orm";
import { getDb } from "../server/db";
import {
  buildLeadScopeCondition,
  buildDealScopeCondition,
  buildClientScopeCondition,
  isRowInScope,
} from "../server/security/phase3ScopeFilters";

function requireFile(file: string, markers: string[]) {
  const full = path.resolve(process.cwd(), file);
  if (!fs.existsSync(full)) throw new Error(`Missing file: ${file}`);
  const text = fs.readFileSync(full, "utf8");
  for (const marker of markers) if (!text.includes(marker)) throw new Error(`Missing marker in ${file}: ${marker}`);
}

const fakeUser = (id: number, teamId: number | null = 1) => ({ id: String(id), teamId, role: "SalesAgent" });

async function main() {
  requireFile("server/security/phase3ScopeFilters.ts", [
    "Phase 3A Reviewed Fix V1",
    'if (scope === "own")',
    'if (scope === "assigned")',
    "aliasFromOwnerColumn",
  ]);
  requireFile("server/routers.ts", ["leadsViewScope", "dealsViewScope", "clientsViewScope"]);
  requireFile("server/_core/trpc.ts", ["phase3Scope", "leadsViewScope", "dealsViewScope", "clientsViewScope"]);

  const db = await getDb();
  if (!db) throw new Error("DATABASE_URL is required for Phase 3A verification");

  // Alias regression: export uses alias `l`. Both own and assigned must compile and execute.
  const leadOwnAlias = buildLeadScopeCondition("own", fakeUser(999999), "l.ownerId");
  await db.execute(sql`SELECT l.id FROM leads l WHERE l.deletedAt IS NULL AND (${leadOwnAlias}) LIMIT 1`);
  const leadAssignedAlias = buildLeadScopeCondition("assigned", fakeUser(999999), "l.ownerId");
  await db.execute(sql`SELECT l.id FROM leads l WHERE l.deletedAt IS NULL AND (${leadAssignedAlias}) LIMIT 1`);

  // Other scoped query builders must also remain valid SQL.
  const dealAssigned = buildDealScopeCondition("assigned", fakeUser(999999), "d");
  await db.execute(sql`SELECT d.id FROM deals d WHERE d.deletedAt IS NULL AND (${dealAssigned}) LIMIT 1`);
  const clientOwn = buildClientScopeCondition("own", fakeUser(999999), "clients");
  await db.execute(sql`SELECT clients.id FROM clients WHERE clients.deletedAt IS NULL AND (${clientOwn}) LIMIT 1`);

  // Basic row semantics that require no seeded records.
  const ownDecision: any = { allowed: true, permission: "leads.view", scope: "own", source: "test" };
  const assignedDecision: any = { allowed: true, permission: "clients.view", scope: "assigned", source: "test" };
  if (!(await isRowInScope("lead", ownDecision, fakeUser(7), { id: 1, ownerId: 7 }))) throw new Error("Lead own must allow owner");
  if (await isRowInScope("lead", ownDecision, fakeUser(7), { id: 1, ownerId: 8 })) throw new Error("Lead own must not broaden to non-owner");
  if (!(await isRowInScope("client", assignedDecision, fakeUser(7), { id: 1, accountManagerId: 7 }))) throw new Error("Client assigned must allow direct account manager");
  if (await isRowInScope("client", assignedDecision, fakeUser(7), { id: 1, accountManagerId: 8 })) throw new Error("Client assigned must deny other account managers");

  console.log(JSON.stringify({
    ok: true,
    phase: "3A-reviewed-fix-v1",
    fixed: ["own-vs-assigned-separation", "lead-export-alias-safety"],
    unsupportedScopes: ["department", "created_by", "custom", "none"],
    unsupportedBehavior: "deny-by-default",
  }));
}

main().catch((error) => {
  console.error("Advanced Permissions Phase 3A reviewed verification failed:", error);
  process.exit(1);
});
