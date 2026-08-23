#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

/**
 * TCRM — Lead Attachment crmFileId Fallback V1
 *
 * Confirmed production failure:
 * - Drive upload succeeds.
 * - crm_files row is inserted with a valid auto-increment ID.
 * - Drizzle $returningId() can yield no usable ID in the live runtime.
 * - storeCrmFile() therefore returns crmFileId=null and LeadProfile stops before attachments.create.
 *
 * Scope:
 * - server/services/crmFileStorage.ts only
 * - no DB schema/migration changes
 * - no Google Drive config changes
 * - no frontend/business-rule changes
 *
 * Usage from the TCRM project root:
 *   node <patch-repo>/patches/lead-attachments/crm-file-id-fallback-v1/apply.mjs --check
 *   node <patch-repo>/patches/lead-attachments/crm-file-id-fallback-v1/apply.mjs --apply
 *   node <patch-repo>/patches/lead-attachments/crm-file-id-fallback-v1/apply.mjs --verify
 */

const mode = process.argv[2] ?? "--check";
const target = path.resolve(process.cwd(), "server/services/crmFileStorage.ts");
const PATCH_MARKER = "CRM_FILE_ID_FALLBACK_V1";

function fail(message, code = 1) {
  console.error(`[crm-file-id-fallback-v1] ${message}`);
  process.exit(code);
}

function info(message) {
  console.log(`[crm-file-id-fallback-v1] ${message}`);
}

if (!fs.existsSync(target)) fail(`target not found: ${target}`, 2);

const originalRaw = fs.readFileSync(target, "utf8");
const usesCRLF = originalRaw.includes("\r\n");
let source = originalRaw.replace(/\r\n/g, "\n");

const functionStartMarker = "export async function storeCrmFile(input: StoreCrmFileInput) {";
const functionEndMarker = "\nexport async function markCrmFileDeletedById";

function getStoreCrmFileRange(input) {
  const start = input.indexOf(functionStartMarker);
  if (start === -1) fail("storeCrmFile() function not found");
  const end = input.indexOf(functionEndMarker, start);
  if (end === -1) fail("storeCrmFile() end marker not found");
  return { start, end };
}

function isPatched(input) {
  const { start, end } = getStoreCrmFileRange(input);
  const segment = input.slice(start, end);
  return segment.includes(PATCH_MARKER)
    && segment.includes("where(eq(crmFiles.storageKey, stored.key))")
    && segment.includes("CRM file row was inserted but its ID could not be resolved");
}

const oldBlock = `    const crmFileId = Number((inserted as any)?.id ?? (inserted as any)?.insertId ?? 0) || null;\n\n    return {`;

const newBlock = `    let crmFileId = Number((inserted as any)?.id ?? (inserted as any)?.insertId ?? 0) || null;\n\n    // ${PATCH_MARKER}: production MySQL/Drizzle can insert the row successfully while $returningId()\n    // yields no usable ID. Resolve the exact row by the generated storage key before returning.\n    if (!crmFileId) {\n      const insertedRows = await db\n        .select({ id: crmFiles.id })\n        .from(crmFiles)\n        .where(eq(crmFiles.storageKey, stored.key))\n        .orderBy(desc(crmFiles.id))\n        .limit(1);\n      crmFileId = Number(insertedRows[0]?.id ?? 0) || null;\n    }\n\n    if (!crmFileId) {\n      throw new Error(\`[CrmFileStorage] CRM file row was inserted but its ID could not be resolved for key "\${stored.key}"\`);\n    }\n\n    return {`;

if (mode === "--check") {
  if (isPatched(source)) {
    info("already patched");
    process.exit(0);
  }
  const { start, end } = getStoreCrmFileRange(source);
  const segment = source.slice(start, end);
  if (!segment.includes(oldBlock)) fail("expected crmFileId derivation block not found in storeCrmFile()");
  if (!source.includes('import { and, desc, eq, inArray, lt, or } from "drizzle-orm";')) {
    fail("expected drizzle imports (desc/eq) are not present");
  }
  info("ready to apply");
  process.exit(0);
}

if (mode === "--apply") {
  if (!isPatched(source)) {
    const { start, end } = getStoreCrmFileRange(source);
    const before = source.slice(0, start);
    const segment = source.slice(start, end);
    const after = source.slice(end);

    if (!segment.includes(oldBlock)) fail("expected crmFileId derivation block not found in storeCrmFile()");
    const patchedSegment = segment.replace(oldBlock, newBlock);
    source = before + patchedSegment + after;
  }

  if (!isPatched(source)) fail("patch application did not reach expected final state");
  const output = usesCRLF ? source.replace(/\n/g, "\r\n") : source;
  fs.writeFileSync(target, output, "utf8");
  info("patch applied successfully");
  process.exit(0);
}

if (mode === "--verify") {
  if (!isPatched(source)) fail("expected fallback markers were not found");
  const { start, end } = getStoreCrmFileRange(source);
  const segment = source.slice(start, end);
  if (segment.includes(oldBlock)) fail("old crmFileId-only return path is still present");
  info("verification passed");
  process.exit(0);
}

fail(`unknown mode: ${mode}`);
