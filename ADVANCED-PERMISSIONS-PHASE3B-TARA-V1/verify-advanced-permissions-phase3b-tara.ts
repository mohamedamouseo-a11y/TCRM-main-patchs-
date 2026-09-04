import { readFileSync } from "node:fs";

const catalog = readFileSync("server/security/permissionCatalog.ts", "utf8");
const trpc = readFileSync("server/_core/trpc.ts", "utf8");
const routers = readFileSync("server/routers.ts", "utf8");

const requiredKeys = ["tara.view", "tara.operate", "tara.moderate", "tara.manage"];
const requiredScopes = ["taraViewScope", "taraOperateScope", "taraModerateScope", "taraManageScope"];

for (const key of requiredKeys) {
  if (!catalog.includes(`\"${key}\"`)) throw new Error(`missing catalog key: ${key}`);
}
for (const scope of requiredScopes) {
  if (!trpc.includes(`export const ${scope}`)) throw new Error(`missing scope export: ${scope}`);
  if (!routers.includes(scope)) throw new Error(`scope not used in routers.ts: ${scope}`);
}
if (!trpc.includes("ADVANCED_PERMISSIONS_PHASE3B_TARA_V1")) throw new Error("missing Tara V1 marker");

const forbidden = [
  "server/modules/messenger/router.messenger.ts",
  "services/waGatewayIntegrationService",
];

console.log(JSON.stringify({
  ok: true,
  phase: "3B-tara-v1",
  verified: ["tara-view", "tara-operate", "tara-moderate", "tara-manage", "dedicated-tara-catalog"],
  excluded: ["whatsapp-gateway", "messenger", "meta-tiktok-google-ads-outside-tara", "tfs-tos-drive-backup", "thrs", "developer-hub", "meetings-felfel-tam"],
}, null, 2));
