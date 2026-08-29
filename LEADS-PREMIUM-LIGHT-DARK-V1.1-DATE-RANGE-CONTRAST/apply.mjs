#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const PATCH_ID = "LEADS-PREMIUM-LIGHT-DARK-V1.1-DATE-RANGE-CONTRAST";
const MARKER_START = "/* BEGIN LEADS DATE RANGE CONTRAST V1.1 */";
const MARKER_END = "/* END LEADS DATE RANGE CONTRAST V1.1 */";
const args = new Set(process.argv.slice(2).filter((arg) => !arg.startsWith("--root=")));
const rootArg = process.argv.slice(2).find((arg) => arg.startsWith("--root="));
const ROOT = path.resolve(rootArg ? rootArg.slice("--root=".length) : "/var/www/TCRM-MAIN");
const TARGET = path.join(ROOT, "client/src/leads-premium.css");

const BLOCK = `\n\n${MARKER_START}\n/* DateRangePicker trigger: readable in Premium Leads Light Mode, preserved in Dark Mode. */\n.fade-in:has(> .slide-up:first-child + [data-slot="card"][class*="rounded-[24px]"]) button#date {\n  color: #181827 !important;\n}\n\n.fade-in:has(> .slide-up:first-child + [data-slot="card"][class*="rounded-[24px]"]) button#date svg {\n  color: #5b6170 !important;\n  opacity: 1 !important;\n}\n\n.fade-in:has(> .slide-up:first-child + [data-slot="card"][class*="rounded-[24px]"]) button#date span.opacity-90 {\n  color: #181827 !important;\n  opacity: 0.78 !important;\n}\n\n.dark .fade-in:has(> .slide-up:first-child + [data-slot="card"][class*="rounded-[24px]"]) button#date,\nbody.dark .fade-in:has(> .slide-up:first-child + [data-slot="card"][class*="rounded-[24px]"]) button#date {\n  color: #f6f7fb !important;\n}\n\n.dark .fade-in:has(> .slide-up:first-child + [data-slot="card"][class*="rounded-[24px]"]) button#date svg,\nbody.dark .fade-in:has(> .slide-up:first-child + [data-slot="card"][class*="rounded-[24px]"]) button#date svg {\n  color: #f6f7fb !important;\n  opacity: 0.95 !important;\n}\n\n.dark .fade-in:has(> .slide-up:first-child + [data-slot="card"][class*="rounded-[24px]"]) button#date span.opacity-90,\nbody.dark .fade-in:has(> .slide-up:first-child + [data-slot="card"][class*="rounded-[24px]"]) button#date span.opacity-90 {\n  color: #f6f7fb !important;\n  opacity: 0.86 !important;\n}\n${MARKER_END}\n`;

function fail(message) {
  console.error(`[${PATCH_ID}] ERROR: ${message}`);
  process.exit(1);
}

function requireTarget() {
  if (!fs.existsSync(TARGET) || !fs.statSync(TARGET).isFile()) {
    fail(`Base Premium Leads stylesheet not found: ${TARGET}. Apply LEADS-PREMIUM-LIGHT-DARK-V1 first.`);
  }
  const css = fs.readFileSync(TARGET, "utf8");
  if (!css.includes("TCRM Leads — Premium Light / Dark Experience")) {
    fail("Expected Premium Leads V1 stylesheet signature is missing. Stop; do not modify unknown CSS.");
  }
  return css;
}

function state(css) {
  const hasStart = css.includes(MARKER_START);
  const hasEnd = css.includes(MARKER_END);
  if (hasStart !== hasEnd) fail("Partial V1.1 marker detected. Stop for manual inspection.");
  return hasStart ? "already-applied" : "ready";
}

function check() {
  const css = requireTarget();
  console.log(`[${PATCH_ID}] CHECK OK`);
  console.log(`root=${ROOT}`);
  console.log(`state=${state(css)}`);
  console.log("scope=UI-only date-range trigger contrast on Leads page");
}

function backup() {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const dir = path.join(ROOT, ".patch-backups", PATCH_ID, stamp);
  fs.mkdirSync(dir, { recursive: true });
  fs.copyFileSync(TARGET, path.join(dir, "leads-premium.css"));
  console.log(`[${PATCH_ID}] backup=${dir}`);
}

function apply() {
  const css = requireTarget();
  const current = state(css);
  if (current === "already-applied") {
    console.log(`[${PATCH_ID}] already applied; no changes made.`);
    verify();
    return;
  }
  backup();
  fs.writeFileSync(TARGET, `${css.trimEnd()}${BLOCK}`, "utf8");
  verify();
  console.log(`[${PATCH_ID}] APPLY OK`);
}

function verify() {
  const css = requireTarget();
  if (state(css) !== "already-applied") fail("V1.1 contrast block not found after apply.");
  const required = [
    "button#date",
    "color: #181827 !important",
    "color: #5b6170 !important",
    "color: #f6f7fb !important",
  ];
  const missing = required.filter((needle) => !css.includes(needle));
  if (missing.length) fail(`Missing expected rule(s): ${missing.join(", ")}`);
  console.log(`[${PATCH_ID}] VERIFY OK`);
  console.log("changed-file=client/src/leads-premium.css");
  console.log("light-date-text=#181827");
  console.log("light-icons=#5b6170");
  console.log("dark-contrast=preserved");
  console.log("business-logic=untouched");
}

if (args.has("--apply")) apply();
else if (args.has("--verify")) verify();
else if (args.has("--check") || args.size === 0) check();
else fail("Usage: node apply.mjs [--check|--apply|--verify] [--root=/var/www/TCRM-MAIN]");
