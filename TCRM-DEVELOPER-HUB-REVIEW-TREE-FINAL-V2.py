#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
ROUTE = ROOT / "server" / "routes" / "developerHub.ts"
RUNTIME = ROOT / "server" / "services" / "developerHubGitHubRuntime.ts"
RUNTIME_TEST = ROOT / "server" / "services" / "developerHubGitHubRuntime.test.ts"
SECURITY_TEST = ROOT / "server" / "services" / "developerHubGitHubSecurity.test.ts"

for path in [ROUTE, RUNTIME, RUNTIME_TEST, SECURITY_TEST]:
    if not path.exists():
        raise SystemExit(f"ERROR: missing expected TCRM file: {path}")

# ---------------------------------------------------------------------------
# 1) Runtime helper: build the reviewed index in isolation, verify it, then
#    atomically install it into the repository's real index.
# ---------------------------------------------------------------------------
runtime = RUNTIME.read_text(encoding="utf-8")

security_import = 'import { isDeveloperHubPatchStatePath } from "./developerHubGitHubSecurity";\n'
if security_import not in runtime:
    import_anchor = 'import { assertCanonicalDeveloperHubGitRoot } from "./developerHubRepositoryRoot";\n'
    if import_anchor not in runtime:
        raise SystemExit("ERROR: runtime import anchor not found")
    runtime = runtime.replace(import_anchor, import_anchor + security_import, 1)

helper_marker = "// DEVELOPER_HUB_DETERMINISTIC_REVIEWED_INDEX_V2"
helper = r'''
// DEVELOPER_HUB_DETERMINISTIC_REVIEWED_INDEX_V2
// Build the exact reviewed candidate tree in an isolated Git index first,
// validate that no Developer Hub rollback-state path is present, then install
// that verified index atomically. This keeps stale/shared real-index state out
// of reviewed pushes while preserving the existing candidate-tree equality
// guards in the route.
export async function materializeReviewedCandidateTreeIndex(
  repoDir: string,
  candidateTree: string,
  baseEnv: NodeJS.ProcessEnv,
): Promise<string> {
  const canonicalRepoDir = assertCanonicalDeveloperHubGitRoot(repoDir);
  const normalized = String(candidateTree || "").trim();
  if (!/^[a-f0-9]{40,64}$/i.test(normalized)) {
    throw new Error("Invalid reviewed candidate tree.");
  }

  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "tcrm-reviewed-index-v2-"));
  const isolatedIndexPath = path.join(tempDir, "index");
  const isolatedEnv: NodeJS.ProcessEnv = { ...baseEnv, GIT_INDEX_FILE: isolatedIndexPath };
  let installPath = "";

  try {
    await execFileAsync("git", ["read-tree", "--reset", normalized], {
      cwd: canonicalRepoDir,
      env: isolatedEnv,
      encoding: "utf8",
      maxBuffer: 4 * 1024 * 1024,
    });

    const { stdout: isolatedPathsRaw } = await execFileAsync(
      "git",
      ["ls-files", "-z", "--cached"],
      {
        cwd: canonicalRepoDir,
        env: isolatedEnv,
        encoding: "utf8",
        maxBuffer: 64 * 1024 * 1024,
      },
    );
    const rollbackStatePath = String(isolatedPathsRaw)
      .split("\0")
      .filter(Boolean)
      .find(isDeveloperHubPatchStatePath);
    if (rollbackStatePath) {
      throw new Error("Reviewed candidate tree contains Developer Hub rollback state.");
    }

    const { stdout: isolatedTreeRaw } = await execFileAsync("git", ["write-tree"], {
      cwd: canonicalRepoDir,
      env: isolatedEnv,
      encoding: "utf8",
      maxBuffer: 1024 * 1024,
    });
    const isolatedTree = String(isolatedTreeRaw).trim();
    if (isolatedTree !== normalized) {
      throw new Error("Isolated reviewed Git index differs from the reviewed candidate tree.");
    }

    const { stdout: realIndexRaw } = await execFileAsync(
      "git",
      ["rev-parse", "--git-path", "index"],
      {
        cwd: canonicalRepoDir,
        env: baseEnv,
        encoding: "utf8",
        maxBuffer: 1024 * 1024,
      },
    );
    const rawRealIndexPath = String(realIndexRaw).trim();
    if (!rawRealIndexPath) throw new Error("Unable to locate the Git index for reviewed push.");
    const realIndexPath = path.isAbsolute(rawRealIndexPath)
      ? path.normalize(rawRealIndexPath)
      : path.resolve(canonicalRepoDir, rawRealIndexPath);

    const realIndexStat = await fs.lstat(realIndexPath).catch((error: any) => {
      if (error?.code === "ENOENT") return null;
      throw error;
    });
    if (realIndexStat && (!realIndexStat.isFile() || realIndexStat.isSymbolicLink())) {
      throw new Error("Git index is not a regular file.");
    }

    const indexLockPath = `${realIndexPath}.lock`;
    const indexLocked = await fs.lstat(indexLockPath)
      .then(() => true)
      .catch((error: any) => {
        if (error?.code === "ENOENT") return false;
        throw error;
      });
    if (indexLocked) throw new Error("Git index is busy; reviewed push was not started.");

    installPath = `${realIndexPath}.tcrm-reviewed-${process.pid}-${crypto.randomBytes(6).toString("hex")}`;
    await fs.copyFile(isolatedIndexPath, installPath);
    await fs.rename(installPath, realIndexPath);
    installPath = "";

    const { stdout: installedTreeRaw } = await execFileAsync("git", ["write-tree"], {
      cwd: canonicalRepoDir,
      env: baseEnv,
      encoding: "utf8",
      maxBuffer: 1024 * 1024,
    });
    const installedTree = String(installedTreeRaw).trim();
    if (installedTree !== normalized) {
      throw new Error("Installed reviewed Git index differs from the reviewed candidate tree.");
    }
    return installedTree;
  } finally {
    if (installPath) await fs.rm(installPath, { force: true }).catch(() => undefined);
    await fs.rm(tempDir, { recursive: true, force: true }).catch(() => undefined);
  }
}
'''

if helper_marker not in runtime:
    anchor = 'export async function createSafeGitEnvironment(repoDir?: string): Promise<SafeGitEnvironment> {'
    if anchor not in runtime:
        raise SystemExit("ERROR: runtime helper insertion anchor not found")
    runtime = runtime.replace(anchor, helper + "\n" + anchor, 1)

RUNTIME.write_text(runtime, encoding="utf-8")

# ---------------------------------------------------------------------------
# 2) Route: always re-derive the current candidate tree in a fresh temp index
#    immediately before mutation, then atomically materialize the exact reviewed
#    tree into the real index. Existing equality/fingerprint guards remain.
# ---------------------------------------------------------------------------
route = ROUTE.read_text(encoding="utf-8")

runtime_import_anchor = '  isFileOperationLocked,\n  runBestEffort,\n'
if '  materializeReviewedCandidateTreeIndex,\n' not in route:
    if runtime_import_anchor not in route:
        raise SystemExit("ERROR: route runtime import anchor not found")
    route = route.replace(
        runtime_import_anchor,
        '  isFileOperationLocked,\n  materializeReviewedCandidateTreeIndex,\n  runBestEffort,\n',
        1,
    )

advanced_old = 'await stageReviewedPreviewFiles(preview.files || [], secureAuth.gitEnv);'
advanced_v1 = 'await stageReviewedCandidateTree(preview.candidateTree, secureAuth.gitEnv);'
advanced_final = '''const reviewedCandidateTreeNow = await createCandidateTreeSha(secureAuth.gitEnv);\n      if (reviewedCandidateTreeNow !== preview.candidateTree) {\n        throw new Error("Project files changed after review.");\n      }\n      await materializeReviewedCandidateTreeIndex(REPO_DIR, preview.candidateTree, secureAuth.gitEnv);'''

legacy_old = 'await stageReviewedPreviewFiles(preview.files || [], securePushAuth.gitEnv);'
legacy_v1 = 'await stageReviewedCandidateTree(preview.candidateTree, securePushAuth.gitEnv);'
legacy_final = '''const reviewedCandidateTreeNow = await createCandidateTreeSha(securePushAuth.gitEnv);\n    if (reviewedCandidateTreeNow !== preview.candidateTree) {\n      throw new Error("Repository changed after review. Review the files again before pushing.");\n    }\n    await materializeReviewedCandidateTreeIndex(REPO_DIR, preview.candidateTree, securePushAuth.gitEnv);'''

if advanced_final not in route:
    if advanced_v1 in route:
        route = route.replace(advanced_v1, advanced_final, 1)
    elif advanced_old in route:
        route = route.replace(advanced_old, advanced_final, 1)
    else:
        raise SystemExit("ERROR: advanced reviewed staging call not found")

if legacy_final not in route:
    if legacy_v1 in route:
        route = route.replace(legacy_v1, legacy_final, 1)
    elif legacy_old in route:
        route = route.replace(legacy_old, legacy_final, 1)
    else:
        raise SystemExit("ERROR: legacy reviewed staging call not found")

required_route_markers = [
    'suppliedFingerprint !== preview.fingerprint',
    'previewFingerprint !== preview.fingerprint',
    'if (stagedTree !== preview.candidateTree) throw new Error("Project files changed after review.");',
    'if (stagedTreeRaw.trim() !== preview.candidateTree)',
    'materializeReviewedCandidateTreeIndex(REPO_DIR, preview.candidateTree, secureAuth.gitEnv)',
    'materializeReviewedCandidateTreeIndex(REPO_DIR, preview.candidateTree, securePushAuth.gitEnv)',
]
for marker in required_route_markers:
    if marker not in route:
        raise SystemExit(f"ERROR: required route safety marker missing: {marker}")

ROUTE.write_text(route, encoding="utf-8")

# ---------------------------------------------------------------------------
# 3) Runtime regression test: prove a stale real index is replaced by exactly
#    the reviewed candidate tree, not merely by static source-string checks.
# ---------------------------------------------------------------------------
runtime_test = RUNTIME_TEST.read_text(encoding="utf-8")
if '  materializeReviewedCandidateTreeIndex,\n' not in runtime_test:
    import_anchor = '  isFileOperationLocked,\n  runBestEffort,\n'
    if import_anchor not in runtime_test:
        raise SystemExit("ERROR: runtime test import anchor not found")
    runtime_test = runtime_test.replace(
        import_anchor,
        '  isFileOperationLocked,\n  materializeReviewedCandidateTreeIndex,\n  runBestEffort,\n',
        1,
    )

runtime_test_marker = 'it("materializes the exact reviewed candidate tree over a stale real index"'
if runtime_test_marker not in runtime_test:
    final_anchor = '''  it("keeps audit failures from changing the main operation result", async () => {'''
    if final_anchor not in runtime_test:
        raise SystemExit("ERROR: runtime test insertion anchor not found")
    regression_test = r'''  it("materializes the exact reviewed candidate tree over a stale real index", async () => {
    const root = await fs.mkdtemp(path.join(os.tmpdir(), "tcrm-reviewed-index-v2-test-"));
    const repo = path.join(root, "repo");
    let safe: Awaited<ReturnType<typeof createSafeGitEnvironment>> | null = null;
    try {
      await execFileAsync("git", ["init", repo]);
      await execFileAsync("git", ["config", "user.name", "Reviewed Index Test"], { cwd: repo });
      await execFileAsync("git", ["config", "user.email", "reviewed-index@example.com"], { cwd: repo });
      await fs.writeFile(path.join(repo, "reviewed.txt"), "base\n");
      await fs.writeFile(path.join(repo, "stale.txt"), "base\n");
      await execFileAsync("git", ["add", "reviewed.txt", "stale.txt"], { cwd: repo });
      await execFileAsync("git", ["commit", "-m", "base"], { cwd: repo });

      await fs.writeFile(path.join(repo, "reviewed.txt"), "reviewed change\n");
      const candidateIndex = path.join(root, "candidate.index");
      const candidateEnv = { ...process.env, GIT_INDEX_FILE: candidateIndex };
      await execFileAsync("git", ["read-tree", "HEAD"], { cwd: repo, env: candidateEnv });
      await execFileAsync("git", ["add", "reviewed.txt"], { cwd: repo, env: candidateEnv });
      const { stdout: candidateTreeRaw } = await execFileAsync("git", ["write-tree"], { cwd: repo, env: candidateEnv });
      const candidateTree = candidateTreeRaw.trim();

      await fs.writeFile(path.join(repo, "stale.txt"), "stale staged change\n");
      await execFileAsync("git", ["add", "stale.txt"], { cwd: repo });
      const { stdout: staleTreeRaw } = await execFileAsync("git", ["write-tree"], { cwd: repo });
      expect(staleTreeRaw.trim()).not.toBe(candidateTree);

      safe = await createSafeGitEnvironment(repo);
      const installedTree = await materializeReviewedCandidateTreeIndex(repo, candidateTree, safe.gitEnv);
      expect(installedTree).toBe(candidateTree);
      const { stdout: realTreeRaw } = await execFileAsync("git", ["write-tree"], { cwd: repo, env: safe.gitEnv });
      expect(realTreeRaw.trim()).toBe(candidateTree);
      const { stdout: stagedNamesRaw } = await execFileAsync("git", ["diff", "--cached", "--name-only"], {
        cwd: repo,
        env: safe.gitEnv,
      });
      expect(stagedNamesRaw.trim().split("\n").filter(Boolean)).toEqual(["reviewed.txt"]);
    } finally {
      await safe?.cleanup();
      await fs.rm(root, { recursive: true, force: true });
    }
  });

'''
    runtime_test = runtime_test.replace(final_anchor, regression_test + final_anchor, 1)

RUNTIME_TEST.write_text(runtime_test, encoding="utf-8")

# ---------------------------------------------------------------------------
# 4) Security/source contract test: align with deterministic V2 behavior while
#    preserving permanent patch-state exclusions and old safety invariants.
# ---------------------------------------------------------------------------
security_test = SECURITY_TEST.read_text(encoding="utf-8")
start_token = '  it("keeps patch rollback state out of every Developer Hub review and explicit staging path", () => {'
start = security_test.find(start_token)
if start < 0:
    raise SystemExit("ERROR: security test contract block not found")
end_token = '\n  });\n\n});'
end = security_test.find(end_token, start)
if end < 0:
    raise SystemExit("ERROR: security test contract block end not found")
end += len('\n  });')
new_contract = r'''  it("keeps patch rollback state out of every Developer Hub review and deterministic reviewed-index path", () => {
    const route = readFileSync(path.resolve(process.cwd(), "server/routes/developerHub.ts"), "utf8");
    expect(route.match(/filterDeveloperHubPatchStateEntries\(parseGitStatusPorcelainZ\(statusRaw\)\)/g)?.length).toBe(3);
    expect(route).toContain("async function stageExplicitWorkingTreePaths");
    const deterministicCalls = route.match(
      /await materializeReviewedCandidateTreeIndex\(REPO_DIR, preview\.candidateTree, (?:secureAuth|securePushAuth)\.gitEnv\);/g,
    ) ?? [];
    expect(deterministicCalls.length).toBeGreaterThanOrEqual(2);
    expect(route).toContain("const reviewedCandidateTreeNow = await createCandidateTreeSha(secureAuth.gitEnv);");
    expect(route).toContain("const reviewedCandidateTreeNow = await createCandidateTreeSha(securePushAuth.gitEnv);");
    expect(route).toContain("await materializeReviewedCandidateTreeIndex(REPO_DIR, preview.candidateTree, secureAuth.gitEnv);");
    expect(route).toContain("await materializeReviewedCandidateTreeIndex(REPO_DIR, preview.candidateTree, securePushAuth.gitEnv);");
    expect(route).toContain("await removeDeveloperHubPatchStateFromIndex(env);");
    expect(route).not.toContain('args: ["add", "-A", "--", "."]');
    expect(route).toContain('if (stagedTree !== preview.candidateTree) throw new Error("Project files changed after review.");');
    expect(route).toContain('if (stagedTreeRaw.trim() !== preview.candidateTree)');
  });'''
security_test = security_test[:start] + new_contract + security_test[end:]
SECURITY_TEST.write_text(security_test, encoding="utf-8")

print("PATCH=TCRM-DEVELOPER-HUB-REVIEW-TREE-FINAL-V2")
print("FIX=DETERMINISTIC_ISOLATED_INDEX_PLUS_ATOMIC_INSTALL")
print("POST_REVIEW_CHANGE_GUARD=FRESH_TEMP_CANDIDATE_TREE")
print("REAL_INDEX_STALE_STATE=ELIMINATED")
print("FINGERPRINT_GUARDS=PRESERVED")
print("TREE_EQUALITY_GUARDS=PRESERVED")
print("RUNTIME_REGRESSION_TEST=ADDED")
print("FILES_CHANGED=server/routes/developerHub.ts,server/services/developerHubGitHubRuntime.ts,server/services/developerHubGitHubRuntime.test.ts,server/services/developerHubGitHubSecurity.test.ts")
