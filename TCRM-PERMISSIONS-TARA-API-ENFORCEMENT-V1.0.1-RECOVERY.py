#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

VERSION = "V1.0.1"
WORKFLOW_ID = "TCRM-PERMISSIONS-TARA-API-ENFORCEMENT-V1.0.1-RECOVERY"
BASELINE = "4fd97e4ae23c66a67907ee148ac49c59516ad099"
ROOT = Path("/var/www/TCRM-MAIN")
POLICY = ROOT / "server/security/corePermissionPolicy.ts"
TEST = ROOT / "server/security/taraPermissionPolicy.test.ts"
EXPECTED = {
    "server/security/corePermissionPolicy.ts",
    "server/security/taraPermissionPolicy.test.ts",
}

def fail(message: str):
    print(f"ERROR={message}", file=sys.stderr)
    raise SystemExit(1)

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

if git("rev-parse", "HEAD") != BASELINE:
    fail("BASELINE_MISMATCH")
if git("diff", "--name-only") or git("diff", "--cached", "--name-only"):
    fail("TRACKED_WORKTREE_NOT_CLEAN")

policy = POLICY.read_text()
test = TEST.read_text()

old_operate = '''const TARA_OPERATE_OPERATIONS = new Set([\n  "testagent",\n  "processqueue",\n  "processvoicequeue",\n  "setconversationstatus",\n  "generatesocialreply",\n  "sendsocialreply",\n  "retrysocialreply",\n  "updatesocialconversation",\n  "createleadfromsocial",\n  "processsocialqueue",\n]);'''
new_operate = '''const TARA_OPERATE_OPERATIONS = new Set([\n  // Tara Moderator operational workspace: safe non-secret configuration/actions.\n  // Keep this list aligned with shared/moderatorOperationalAccess.ts.\n  "moderationsaveoperationalsettings",\n  "savecampaign",\n  "deletecampaign",\n  "savequalificationfield",\n  "deletequalificationfield",\n  "saveknowledge",\n  "deleteknowledge",\n  "savefollowuprule",\n  "deletefollowuprule",\n  "testagent",\n  "processqueue",\n  "processvoicequeue",\n  "setconversationstatus",\n  "generatesocialreply",\n  "sendsocialreply",\n  "retrysocialreply",\n  "updatesocialconversation",\n  "createleadfromsocial",\n  "processsocialqueue",\n]);'''

if policy.count(old_operate) != 1:
    fail("OPERATE_ANCHOR_DRIFT")
policy = policy.replace(old_operate, new_operate, 1)

marker = '''describe("Tara API permission enforcement V1.0.0", () => {'''
if marker not in test:
    fail("TEST_BASELINE_ANCHOR_DRIFT")
if 'describe("Tara API permission enforcement V1.0.1 recovery"' in test:
    fail("RECOVERY_TEST_ALREADY_PRESENT")

recovery_tests = r'''

describe("Tara API permission enforcement V1.0.1 recovery", () => {
  it("keeps Moderator operational workspace mutations behind tara.operate instead of tara.manage", () => {
    const operations = [
      "tara.moderation.saveOperationalSettings",
      "tara.saveCampaign",
      "tara.deleteCampaign",
      "tara.saveQualificationField",
      "tara.deleteQualificationField",
      "tara.saveKnowledge",
      "tara.deleteKnowledge",
      "tara.saveFollowupRule",
      "tara.deleteFollowupRule",
    ];
    for (const item of operations) {
      expect(resolveCorePermissionKey(item, "mutation"), item).toBe("tara.operate");
    }
  });

  it("preserves Moderator-safe Tara reads and runtime actions", () => {
    expect(resolveCorePermissionKey("tara.dashboard", "query")).toBe("tara.view");
    expect(resolveCorePermissionKey("tara.listCampaigns", "query")).toBe("tara.view");
    expect(resolveCorePermissionKey("tara.logs", "query")).toBe("tara.view");
    expect(resolveCorePermissionKey("tara.testAgent", "mutation")).toBe("tara.operate");
    expect(resolveCorePermissionKey("tara.processQueue", "mutation")).toBe("tara.operate");
    expect(resolveCorePermissionKey("tara.setConversationStatus", "mutation")).toBe("tara.operate");
  });

  it("keeps technical/admin Tara surfaces fail-closed behind tara.manage", () => {
    for (const [path, type] of [
      ["tara.saveSettings", "mutation"],
      ["tara.saveProviderConfiguration", "mutation"],
      ["tara.saveVoiceSettings", "mutation"],
      ["tara.saveSocialApiSettings", "mutation"],
      ["tara.createSocialChannel", "mutation"],
      ["tara.startMetaOAuth", "mutation"],
      ["tara.getTikTokBusinessSettings", "query"],
      ["tara.moderation.managementSnapshot", "query"],
      ["tara.moderation.saveModerator", "mutation"],
      ["tara.futureUnknownOperation", "mutation"],
    ] as const) {
      expect(resolveCorePermissionKey(path, type), `${type} ${path}`).toBe("tara.manage");
    }
  });
});
'''

test = test.rstrip() + recovery_tests + "\n"

POLICY.write_text(policy)
TEST.write_text(test)

changed = set(filter(None, git("diff", "--name-only").splitlines()))
if changed != EXPECTED:
    fail("UNEXPECTED_DIRTY_SET:" + ",".join(sorted(changed)))

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print("PATCH_APPLIED=YES")
print("FILES_CHANGED=" + ",".join(sorted(changed)))
