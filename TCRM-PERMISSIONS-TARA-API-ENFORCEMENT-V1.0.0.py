#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "TARA"
PHASE = "API-ENFORCEMENT"
VERSION = "V1.0.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-TARA-API-ENFORCEMENT-V1.0.0"
EXPECTED_BASELINE = "a23cf0ef13241145ae4d5736826fdd33c06ebf91"
PROJECT = Path("/var/www/TCRM-MAIN")
EXPECTED_FILES = {
    "server/security/corePermissionPolicy.ts",
    "server/security/taraPermissionPolicy.test.ts",
}


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=PROJECT, text=True).strip()


def fail(code: str, detail: str = "") -> None:
    print(f"WORKFLOW_SERIES={WORKFLOW_SERIES}")
    print(f"MODULE={MODULE}")
    print(f"PHASE={PHASE}")
    print(f"VERSION={VERSION}")
    print(f"WORKFLOW_ID={WORKFLOW_ID}")
    print("PATCH_APPLIED=NO")
    print(f"ERROR={code}")
    if detail:
        print(f"ERROR_DETAIL={detail}")
    print("FILES_CHANGED=NONE")
    print("READY_FOR_TESTS=NO")
    raise SystemExit(1)


if not PROJECT.exists():
    fail("PROJECT_NOT_FOUND", str(PROJECT))

head = run("git", "rev-parse", "HEAD")
if head != EXPECTED_BASELINE:
    fail("BASELINE_MISMATCH", f"expected={EXPECTED_BASELINE} actual={head}")

tracked_dirty = set(filter(None, run("git", "diff", "--name-only").splitlines()))
tracked_dirty |= set(filter(None, run("git", "diff", "--cached", "--name-only").splitlines()))
if tracked_dirty:
    fail("PREEXISTING_TRACKED_DIFF", ",".join(sorted(tracked_dirty)))

policy_path = PROJECT / "server/security/corePermissionPolicy.ts"
test_path = PROJECT / "server/security/taraPermissionPolicy.test.ts"
if not policy_path.exists():
    fail("POLICY_FILE_MISSING", str(policy_path))
if test_path.exists():
    fail("TEST_FILE_ALREADY_EXISTS", str(test_path))

policy = policy_path.read_text()

marker = "// TCRM_PERMISSIONS_TARA_API_V1"
if marker in policy:
    fail("PATCH_ALREADY_PRESENT")

set_anchor = '''\nfunction hasAny(value: string, words: readonly string[]) {\n'''
if policy.count(set_anchor) != 1:
    fail("SET_ANCHOR_DRIFT", f"count={policy.count(set_anchor)}")

sets = r'''

// TCRM_PERMISSIONS_TARA_API_V1
// Tara has four permission levels. Keep passive/operator/moderator/admin surfaces
// explicit and send every unknown future Tara operation to tara.manage fail-closed.
const TARA_VIEW_OPERATIONS = new Set([
  "moderationprofile",
  "moderationoperationalsettings",
  "moderationoverview",
  "moderationnotes",
  "dashboard",
  "listcampaigns",
  "listqualificationfields",
  "listknowledge",
  "listfollowuprules",
  "listassignableusers",
  "listcrmcampaigns",
  "logs",
  "getconversationcontext",
  "socialoverview",
]);

const TARA_OPERATE_OPERATIONS = new Set([
  "testagent",
  "processqueue",
  "processvoicequeue",
  "setconversationstatus",
  "generatesocialreply",
  "sendsocialreply",
  "retrysocialreply",
  "updatesocialconversation",
  "createleadfromsocial",
  "processsocialqueue",
]);

const TARA_MODERATE_OPERATIONS = new Set([
  "moderationgeneratereply",
  "moderationsendreply",
  "moderationretryreply",
  "moderationupdateconversation",
  "moderationaddnote",
  "moderationsuggestknowledge",
]);
'''
policy = policy.replace(set_anchor, sets + set_anchor, 1)

route_anchor = '''  if (root === "waGateway") {\n    if (WA_GATEWAY_VIEW_OPERATIONS.has(operation)) return "whatsapp.view";\n    if (WA_GATEWAY_SEND_OPERATIONS.has(operation)) return "whatsapp.send";\n    return "whatsapp.manage";\n  }\n\n  const module = moduleFromPath(path);\n'''
if policy.count(route_anchor) != 1:
    fail("ROUTE_ANCHOR_DRIFT", f"count={policy.count(route_anchor)}")

route_replacement = '''  if (root === "waGateway") {\n    if (WA_GATEWAY_VIEW_OPERATIONS.has(operation)) return "whatsapp.view";\n    if (WA_GATEWAY_SEND_OPERATIONS.has(operation)) return "whatsapp.send";\n    return "whatsapp.manage";\n  }\n\n  // TCRM_PERMISSIONS_TARA_API_V1\n  // Existing Tara role/profile/account-scope checks remain additive. This layer\n  // only selects the catalog permission at the protectedProcedure boundary.\n  if (root === "tara") {\n    if (TARA_VIEW_OPERATIONS.has(operation)) return "tara.view";\n    if (TARA_OPERATE_OPERATIONS.has(operation)) return "tara.operate";\n    if (TARA_MODERATE_OPERATIONS.has(operation)) return "tara.moderate";\n\n    // Technical settings, provider/voice/channel configuration, moderator\n    // administration, and unknown future Tara operations fail closed here.\n    return "tara.manage";\n  }\n\n  const module = moduleFromPath(path);\n'''
policy = policy.replace(route_anchor, route_replacement, 1)
policy_path.write_text(policy)

test_path.write_text(r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { resolveCorePermissionKey } from "./corePermissionPolicy";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = readFileSync(path.join(here, "corePermissionPolicy.ts"), "utf8");

describe("Tara API permission enforcement V1.0.0", () => {
  it("maps passive Tara reads to tara.view", () => {
    const paths = [
      "tara.moderation.profile",
      "tara.moderation.operationalSettings",
      "tara.moderation.overview",
      "tara.moderation.notes",
      "tara.dashboard",
      "tara.listCampaigns",
      "tara.listQualificationFields",
      "tara.listKnowledge",
      "tara.listFollowupRules",
      "tara.listAssignableUsers",
      "tara.listCrmCampaigns",
      "tara.logs",
      "tara.getConversationContext",
      "tara.socialOverview",
    ];
    for (const item of paths) {
      expect(resolveCorePermissionKey(item, "query"), item).toBe("tara.view");
    }
  });

  it("maps normal Tara runtime/operator mutations to tara.operate", () => {
    const paths = [
      "tara.testAgent",
      "tara.processQueue",
      "tara.processVoiceQueue",
      "tara.setConversationStatus",
      "tara.generateSocialReply",
      "tara.sendSocialReply",
      "tara.retrySocialReply",
      "tara.updateSocialConversation",
      "tara.createLeadFromSocial",
      "tara.processSocialQueue",
    ];
    for (const item of paths) {
      expect(resolveCorePermissionKey(item, "mutation"), item).toBe("tara.operate");
    }
  });

  it("maps Tara moderator actions to tara.moderate", () => {
    const paths = [
      "tara.moderation.generateReply",
      "tara.moderation.sendReply",
      "tara.moderation.retryReply",
      "tara.moderation.updateConversation",
      "tara.moderation.addNote",
      "tara.moderation.suggestKnowledge",
    ];
    for (const item of paths) {
      expect(resolveCorePermissionKey(item, "mutation"), item).toBe("tara.moderate");
    }
  });

  it("fails Tara administration and unknown future operations closed behind tara.manage", () => {
    const cases: Array<[string, string]> = [
      ["tara.saveSettings", "mutation"],
      ["tara.getProviderConfiguration", "query"],
      ["tara.saveProviderConfiguration", "mutation"],
      ["tara.getVoiceSettings", "query"],
      ["tara.saveVoiceSettings", "mutation"],
      ["tara.createSocialChannel", "mutation"],
      ["tara.moderation.managementSnapshot", "query"],
      ["tara.moderation.saveModerator", "mutation"],
      ["tara.futureTechnicalControl", "query"],
      ["tara.futureTechnicalControl", "mutation"],
    ];
    for (const [item, type] of cases) {
      expect(resolveCorePermissionKey(item, type), `${type} ${item}`).toBe("tara.manage");
    }
    expect(source).toContain('if (root === "tara")');
    expect(source).toContain('return "tara.manage";');
  });
});
''')

changed = set(filter(None, run("git", "diff", "--name-only").splitlines()))
if changed != EXPECTED_FILES:
    fail("UNEXPECTED_DIRTY_SET", f"expected={','.join(sorted(EXPECTED_FILES))} actual={','.join(sorted(changed))}")

print(f"WORKFLOW_SERIES={WORKFLOW_SERIES}")
print(f"MODULE={MODULE}")
print(f"PHASE={PHASE}")
print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print("PATCH_APPLIED=YES")
print(f"BASELINE={EXPECTED_BASELINE}")
print("TARA_VIEW_API_GATE=YES")
print("TARA_OPERATE_API_GATE=YES")
print("TARA_MODERATE_API_GATE=YES")
print("TARA_MANAGE_FAIL_CLOSED=YES")
print("EXISTING_TARA_AUTHORIZATION_PRESERVED=YES")
print("ROLE_HARDCODING_CHANGED=NO")
print("FILES_CHANGED=" + ",".join(sorted(changed)))
print("READY_FOR_TESTS=YES")
