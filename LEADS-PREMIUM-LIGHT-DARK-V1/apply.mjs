#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PATCH_ID = "LEADS-PREMIUM-LIGHT-DARK-V1";
const PATCH_DIR = path.dirname(fileURLToPath(import.meta.url));
const SOURCE_CSS = path.join(PATCH_DIR, "leads-premium.css");
const STYLE_LINK = '    <link rel="stylesheet" href="/src/leads-premium.css" />';
const args = new Set(process.argv.slice(2).filter((arg) => !arg.startsWith("--root=")));
const rootArg = process.argv.slice(2).find((arg) => arg.startsWith("--root="));
const ROOT = path.resolve(rootArg ? rootArg.slice("--root=".length) : "/var/www/TCRM");
const INDEX = path.join(ROOT, "client/index.html");
const TARGET_CSS = path.join(ROOT, "client/src/leads-premium.css");
const LEADS_PAGE = path.join(ROOT, "client/src/pages/LeadsList.tsx");

function fail(message) {
  console.error(`[${PATCH_ID}] ERROR: ${message}`);
  process.exit(1);
}

function requireFile(file, label) {
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) fail(`${label} not found: ${file}`);
}

function read(file) {
  return fs.readFileSync(file, "utf8");
}

function linkCount(indexText) {
  return (indexText.match(/<link rel="stylesheet" href="\/src\/leads-premium\.css" \/>/g) || []).length;
}

function validateProjectShape() {
  requireFile(SOURCE_CSS, "Patch CSS asset");
  requireFile(INDEX, "TCRM client index");
  requireFile(LEADS_PAGE, "TCRM Leads page");

  const leads = read(LEADS_PAGE);
  const requiredMarkers = ["slide-up", "rounded-[24px]", "data-slot=\"card\""];
  const missing = requiredMarkers.filter((marker) => !leads.includes(marker));
  if (missing.length) {
    fail(`Leads DOM signature drift detected. Missing marker(s): ${missing.join(", ")}. Stop; do not force-apply.`);
  }
}

function check() {
  validateProjectShape();
  const indexText = read(INDEX);
  const sourceCss = read(SOURCE_CSS);
  const count = linkCount(indexText);

  if (count > 1) fail(`Duplicate premium Leads stylesheet links found in client/index.html (${count}).`);
  if (fs.existsSync(TARGET_CSS) && read(TARGET_CSS) !== sourceCss) {
    fail("client/src/leads-premium.css already exists with different content. Stop to avoid overwriting unrelated work.");
  }

  const state = count === 1 && fs.existsSync(TARGET_CSS) && read(TARGET_CSS) === sourceCss
    ? "already-applied"
    : "ready";

  console.log(`[${PATCH_ID}] CHECK OK`);
  console.log(`root=${ROOT}`);
  console.log(`state=${state}`);
  console.log("scope=UI-only; Leads Light/Dark premium styling");
}

function backupTargets() {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const backupDir = path.join(ROOT, ".patch-backups", PATCH_ID, stamp);
  fs.mkdirSync(backupDir, { recursive: true });
  fs.copyFileSync(INDEX, path.join(backupDir, "client-index.html"));
  if (fs.existsSync(TARGET_CSS)) fs.copyFileSync(TARGET_CSS, path.join(backupDir, "leads-premium.css"));
  console.log(`[${PATCH_ID}] backup=${backupDir}`);
}

function apply() {
  check();
  const sourceCss = read(SOURCE_CSS);
  let indexText = read(INDEX);

  if (linkCount(indexText) === 1 && fs.existsSync(TARGET_CSS) && read(TARGET_CSS) === sourceCss) {
    console.log(`[${PATCH_ID}] already applied; no changes made.`);
    return;
  }

  backupTargets();
  fs.mkdirSync(path.dirname(TARGET_CSS), { recursive: true });
  fs.writeFileSync(TARGET_CSS, sourceCss, "utf8");

  if (linkCount(indexText) === 0) {
    const fontLinkPattern = /^(\s*<link id="crm-font-link"[^\n]*\/>)/m;
    if (fontLinkPattern.test(indexText)) {
      indexText = indexText.replace(fontLinkPattern, `$1\n${STYLE_LINK}`);
    } else if (indexText.includes("</head>")) {
      indexText = indexText.replace("</head>", `${STYLE_LINK}\n</head>`);
    } else {
      fail("Could not find a safe insertion point in client/index.html.");
    }
    fs.writeFileSync(INDEX, indexText, "utf8");
  }

  verify();
  console.log(`[${PATCH_ID}] APPLY OK`);
}

function verify() {
  validateProjectShape();
  requireFile(TARGET_CSS, "Installed premium Leads stylesheet");
  const sourceCss = read(SOURCE_CSS);
  const targetCss = read(TARGET_CSS);
  const indexText = read(INDEX);

  if (targetCss !== sourceCss) fail("Installed CSS does not match the official patch asset.");
  if (linkCount(indexText) !== 1) fail("client/index.html must contain exactly one premium Leads stylesheet link.");

  console.log(`[${PATCH_ID}] VERIFY OK`);
  console.log("changed-files=client/src/leads-premium.css, client/index.html");
  console.log("business-logic=untouched");
  console.log("backend-api-db=untouched");
}

if (args.has("--apply")) apply();
else if (args.has("--verify")) verify();
else if (args.has("--check") || args.size === 0) check();
else fail("Usage: node apply.mjs [--check|--apply|--verify] [--root=/var/www/TCRM]");
