#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "server" / "services" / "developerHubGitHubSecurity.test.ts"
ROUTE = ROOT / "server" / "routes" / "developerHub.ts"

for path in (TARGET, ROUTE):
    if not path.exists():
        raise SystemExit(f"ERROR: missing required file: {path}")

route_text = ROUTE.read_text(encoding="utf-8")
required_route_markers = [
    "// DEVELOPER_HUB_REVIEW_TREE_FIX_V1",
    "async function stageReviewedCandidateTree(",
    "await stageReviewedCandidateTree(preview.candidateTree, secureAuth.gitEnv);",
    "await stageReviewedCandidateTree(preview.candidateTree, securePushAuth.gitEnv);",
    'if (stagedTree !== preview.candidateTree) throw new Error("Project files changed after review.");',
    'if (stagedTreeRaw.trim() !== preview.candidateTree)',
]
for marker in required_route_markers:
    if marker not in route_text:
        raise SystemExit(f"ERROR: Review Tree Fix V1 is not fully present; missing: {marker}")

text = TARGET.read_text(encoding="utf-8")

old = '''// Controlled Auto Push V2R16.2 security-test alignment
  it("keeps patch rollback state out of every Developer Hub review and explicit staging path", () => {
    const route = readFileSync(path.resolve(process.cwd(), "server/routes/developerHub.ts"), "utf8");
    expect(route.match(/filterDeveloperHubPatchStateEntries\\(parseGitStatusPorcelainZ\\(statusRaw\\)\\)/g)?.length).toBe(3);
    expect(route).toContain("async function stageExplicitWorkingTreePaths");
    expect(route).toContain("async function stageReviewedPreviewFiles");
    const reviewedStageCalls = route.match(
      /await stageReviewedPreviewFiles\\(preview\\.files \\|\\| \\[\\], (?:secureAuth|securePushAuth)\\.gitEnv\\);/g,
    ) ?? [];
    expect(reviewedStageCalls.length).toBeGreaterThanOrEqual(2);
    expect(route).toContain("await stageReviewedPreviewFiles(preview.files || [], secureAuth.gitEnv);");
    expect(route).toContain("await stageReviewedPreviewFiles(preview.files || [], securePushAuth.gitEnv);");
    expect(route).toContain("await removeDeveloperHubPatchStateFromIndex(env);");
    expect(route).not.toContain('args: ["add", "-A", "--", "."]');
  });
'''

new = '''// Controlled Auto Push V2R16.2 + Review Tree Fix V1 security-test alignment
  it("keeps patch rollback state out of every Developer Hub review and exact reviewed-tree staging path", () => {
    const route = readFileSync(path.resolve(process.cwd(), "server/routes/developerHub.ts"), "utf8");
    expect(route.match(/filterDeveloperHubPatchStateEntries\\(parseGitStatusPorcelainZ\\(statusRaw\\)\\)/g)?.length).toBe(3);
    expect(route).toContain("async function stageExplicitWorkingTreePaths");
    expect(route).toContain("async function stageReviewedCandidateTree");
    const reviewedStageCalls = route.match(
      /await stageReviewedCandidateTree\\(preview\\.candidateTree, (?:secureAuth|securePushAuth)\\.gitEnv\\);/g,
    ) ?? [];
    expect(reviewedStageCalls.length).toBeGreaterThanOrEqual(2);
    expect(route).toContain("await stageReviewedCandidateTree(preview.candidateTree, secureAuth.gitEnv);");
    expect(route).toContain("await stageReviewedCandidateTree(preview.candidateTree, securePushAuth.gitEnv);");
    expect(route).toContain('await execGit(["read-tree", normalized], { env });');
    expect(route).toContain("await removeDeveloperHubPatchStateFromIndex(env);");
    expect(route).toContain('if (stagedTree !== preview.candidateTree) throw new Error("Project files changed after review.");');
    expect(route).toContain("if (stagedTreeRaw.trim() !== preview.candidateTree)");
    expect(route).not.toContain('args: ["add", "-A", "--", "."]');
  });
'''

if old in text:
    if text.count(old) != 1:
        raise SystemExit(f"ERROR: old security-test block count={text.count(old)}; refusing unsafe patch")
    text = text.replace(old, new, 1)
elif new in text:
    print("PATCH_ALREADY_APPLIED=YES")
else:
    raise SystemExit("ERROR: expected security-test block not found; refusing unsafe patch")

TARGET.write_text(text, encoding="utf-8")

print("PATCH=TCRM-DEVELOPER-HUB-REVIEW-TREE-FIX-V1-1-TEST-ALIGNMENT")
print("TEST_CONTRACT=EXACT_REVIEWED_CANDIDATE_TREE")
print("ROLLBACK_STATE_GUARD_PRESERVED=YES")
print("TREE_EQUALITY_ASSERTIONS_PRESERVED=YES")
print("FILES_CHANGED=server/services/developerHubGitHubSecurity.test.ts")
