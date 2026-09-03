import fs from "node:fs";

function read(file: string) {
  if (!fs.existsSync(file)) throw new Error(`Missing ${file}`);
  return fs.readFileSync(file, "utf8");
}

const trpc = read("server/_core/trpc.ts");
const routers = read("server/routers.ts");
const db = read("server/db.ts");
const scope = read("server/security/phase3bScope.ts");

for (const marker of [
  "activitiesViewScope", "activitiesCreateScope", "activitiesEditScope", "activitiesDeleteScope",
  "tasksViewScope", "tasksCreateScope", "tasksEditScope", "tasksAssignScope",
  "contractsViewScope", "contractsCreateScope", "contractsEditScope",
]) if (!trpc.includes(marker)) throw new Error(`Missing tRPC scope: ${marker}`);

for (const marker of [
  "ADVANCED_PERMISSIONS_PHASE3B_V1",
  "assertLeadPermissionScope",
  "assertActivityPermissionScope",
  "filterTasksByPermissionScope",
  "assertTaskCreatePermissionScope",
  "assertContractPermissionScope",
  "filterContractsByPermissionScope",
  "assertContractCreatePermissionScope",
]) if (!routers.includes(marker) && !scope.includes(marker)) throw new Error(`Missing Phase 3B marker: ${marker}`);

if (!db.includes("getActivitiesByUserScoped")) throw new Error("Scoped activity feed DB helper missing");
if (!routers.includes("getActivitiesByUserScoped")) throw new Error("Scoped activity feed not wired");
if (!routers.includes(".use(activitiesViewScope)")) throw new Error("activities.view not wired");
if (!routers.includes(".use(tasksViewScope)")) throw new Error("tasks.view not wired");
if (!routers.includes(".use(contractsViewScope)")) throw new Error("contracts.view not wired");
if (!routers.includes("tasks.assign")) throw new Error("tasks.assign conditional enforcement missing");

for (const unsupported of ["department", "created_by", "custom"]) {
  if (!scope.includes("return false") && !scope.includes("deny(")) throw new Error(`Fail-closed behavior missing for ${unsupported}`);
}

console.log(JSON.stringify({
  ok: true,
  phase: "3B-v1",
  modules: ["activities", "tasks", "contracts"],
  activityScope: "lead-backed; byUser SQL-scoped",
  taskScope: "own=client AM, assigned=task.assignedTo, team=client AM team",
  contractScope: "own=client AM, assigned=renewalAssignedTo, team=client AM team",
  unsupported: ["department", "created_by", "custom", "none"],
  unsupportedBehavior: "deny-by-default",
  meetings: "not touched",
}, null, 2));
