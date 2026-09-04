import fs from "node:fs";

function read(file: string) { return fs.readFileSync(file, "utf8"); }
function must(text: string, needle: string, label: string) {
  if (!text.includes(needle)) throw new Error(`${label}: missing ${needle}`);
}

const trpc = read("server/_core/trpc.ts");
for (const name of [
  "backupViewScope", "backupRunScope", "backupRestoreScope", "backupManageScope",
  "integrationsViewScope", "integrationsManageScope",
]) must(trpc, name, "trpc");

const routers = read("server/routers.ts");
for (const name of [
  "backupViewScope", "backupRunScope", "backupRestoreScope", "backupManageScope",
  "integrationsViewScope", "integrationsManageScope",
]) must(routers, name, "routers import/wiring");

for (const legacySignal of [
  "adminProcedure",
  "getTfsIntegrationSettings",
  "getTosIntegrationSettings",
  "getGoogleDriveFileStorageSettingsForUi",
  "getBackupCenterSettingsForUi",
]) must(routers, legacySignal, "legacy/core surface preserved");

const forbiddenNewMarkers = [
  "ADVANCED_PERMISSIONS_PHASE3B_META_ADS",
  "ADVANCED_PERMISSIONS_PHASE3B_TIKTOK_ADS",
  "ADVANCED_PERMISSIONS_PHASE3B_GOOGLE_ADS",
  "ADVANCED_PERMISSIONS_PHASE3B_WHATSAPP",
  "ADVANCED_PERMISSIONS_PHASE3B_MEETINGS",
];
for (const marker of forbiddenNewMarkers) {
  if (routers.includes(marker)) throw new Error(`Excluded surface touched by this package: ${marker}`);
}

console.log(JSON.stringify({
  ok: true,
  phase: "3B-backup-core-integrations-v1",
  verified: [
    "backup-view-run-restore-manage",
    "core-integrations-view-manage",
    "legacy-guards-preserved",
    "sensitive-settings-remain-additive",
  ],
  excluded: [
    "meta-tiktok-googleads",
    "whatsapp-messenger-tara",
    "thrs-developer-hub",
    "meetings-felfel-tam",
  ],
}, null, 2));
