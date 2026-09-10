#!/usr/bin/env python3
from pathlib import Path
from urllib.request import urlopen

ROOT = Path.cwd()
SECURITY_TEST = ROOT / "server" / "services" / "developerHubGitHubSecurity.test.ts"
if not SECURITY_TEST.exists():
    raise SystemExit(f"ERROR: missing expected TCRM file: {SECURITY_TEST}")

text = SECURITY_TEST.read_text(encoding="utf-8")

old_contract = '''// Controlled Auto Push V2R16.2 security-test alignment
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

v1_contract = '''// Controlled Auto Push V2R16.2 + Review Tree Fix V1 security-test alignment
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

# Normalize the already-applied V1.1 static contract so the cumulative V2 patch
# can replace it deterministically. If the original contract is already present,
# leave it as-is.
if v1_contract in text:
    text = text.replace(v1_contract, old_contract, 1)
    SECURITY_TEST.write_text(text, encoding="utf-8")
elif old_contract not in text and "deterministic reviewed-index path" not in text:
    raise SystemExit("ERROR: unsupported Developer Hub security-test contract state")

url = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TCRM-main-patchs-/main/TCRM-DEVELOPER-HUB-REVIEW-TREE-FINAL-V2.py"
try:
    source = urlopen(url, timeout=30).read().decode("utf-8")
except Exception as exc:
    raise SystemExit(f"ERROR: unable to fetch cumulative V2 patch: {exc}")

namespace = {"__name__": "__main__", "__file__": url}
exec(compile(source, url, "exec"), namespace, namespace)

print("PATCH_WRAPPER=TCRM-DEVELOPER-HUB-REVIEW-TREE-FINAL-V2-1")
print("CUMULATIVE_FINAL_FIX=YES")
