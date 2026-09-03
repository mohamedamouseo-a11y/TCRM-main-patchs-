import fs from "node:fs";
import path from "node:path";

function read(file: string) {
  const full = path.resolve(process.cwd(), file);
  if (!fs.existsSync(full)) throw new Error(`Missing file: ${file}`);
  return fs.readFileSync(full, "utf8");
}

const routers = read("server/routers.ts");
const db = read("server/db.ts");

if (!routers.includes("ADVANCED_PERMISSIONS_PHASE3A_FIX2_V1")) {
  throw new Error("Fix2 marker missing from server/routers.ts");
}
if (!routers.includes("getDealsScoped,")) {
  throw new Error("getDealsScoped import missing from server/routers.ts");
}
if (!routers.includes("getDealsScoped(dealPermissionScopeSql(ctx))")) {
  throw new Error("Phase 3A deals scoped list usage missing");
}
if (!db.includes("export async function getDealsScoped")) {
  throw new Error("getDealsScoped export missing from server/db.ts");
}

console.log(JSON.stringify({
  ok: true,
  phase: "3A-reviewed-fix2-v1",
  fixed: ["missing-getDealsScoped-import"],
  changed: ["server/routers.ts"],
}, null, 2));
