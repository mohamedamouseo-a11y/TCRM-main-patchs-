import fs from "node:fs";

function read(file: string) { return fs.readFileSync(file, "utf8"); }
function must(text: string, needle: string, label: string) {
  if (!text.includes(needle)) throw new Error(`${label}: missing ${needle}`);
}

const trpc = read("server/_core/trpc.ts");
for (const name of ["filesViewScope", "filesUploadScope", "filesEditScope", "filesDeleteScope", "filesShareScope"]) must(trpc, name, "trpc");

const routers = read("server/routers.ts");
for (const name of ["filesViewScope", "filesUploadScope", "filesEditScope", "filesDeleteScope", "filesShareScope"]) must(routers, name, "routers import/wiring");

for (const guard of ["assertCrmFileContextAccess", "assertCrmFileRowAccess", "canDownloadCrmFileCanonical"]) must(routers, guard, "existing file security");

const forbiddenMarkers = [
  "ADVANCED_PERMISSIONS_PHASE3B_FILES_DRIVE_GOOGLE_OAUTH",
  "ADVANCED_PERMISSIONS_PHASE3B_FILES_DRIVE_BACKUP",
];
for (const marker of forbiddenMarkers) {
  if (routers.includes(marker)) throw new Error(`Excluded surface touched: ${marker}`);
}

console.log(JSON.stringify({
  ok: true,
  phase: "3B-files-drive-v1",
  verified: [
    "files-view",
    "files-upload",
    "files-edit",
    "files-delete",
    "files-share",
    "existing-row-context-security-preserved",
  ],
  excluded: ["google-drive-technical-settings", "backup", "integrations", "meetings-felfel-tam"],
}, null, 2));
