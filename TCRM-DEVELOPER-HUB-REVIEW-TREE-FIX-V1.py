#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "server" / "routes" / "developerHub.ts"

if not TARGET.exists():
    raise SystemExit(f"ERROR: missing target file: {TARGET}")

text = TARGET.read_text(encoding="utf-8")

helper_anchor = '''async function stageReviewedPreviewFiles(
  files: ReadonlyArray<{ status?: string; path?: string; originalPath?: string; direction?: string }>,
  env: NodeJS.ProcessEnv,
) {
  const paths: string[] = [];
  for (const file of files) {
    if (file.direction === "remote" || String(file.status || "").trim() === "C") continue;
    if (file.path && !isDeveloperHubPatchStatePath(file.path)) paths.push(file.path);
    if (file.originalPath && !isDeveloperHubPatchStatePath(file.originalPath)) paths.push(file.originalPath);
  }
  await stageExplicitPaths(paths, env);
  await removeDeveloperHubPatchStateFromIndex(env);
}
'''

helper_replacement = helper_anchor + '''
// DEVELOPER_HUB_REVIEW_TREE_FIX_V1
// The preview candidate is built from a fresh temporary index (HEAD + reviewed
// working-tree paths). Replaying only those paths into the process' existing
// index can preserve stale staged entries and produce a different tree even
// though the reviewed working tree itself has not changed. Load the exact
// reviewed candidate tree into the execution index instead. The execute route
// has already recomputed and fingerprint-verified this candidate immediately
// before mutation, and the existing write-tree equality guard remains active.
async function stageReviewedCandidateTree(
  candidateTree: string,
  env: NodeJS.ProcessEnv,
) {
  const normalized = String(candidateTree || "").trim();
  if (!/^[a-f0-9]{40,64}$/i.test(normalized)) {
    throw new Error("Invalid reviewed candidate tree.");
  }
  await execGit(["read-tree", normalized], { env });
  // Candidate creation already excludes Developer Hub patch-state files. Keep
  // this defense-in-depth cleanup; it should be a no-op for a valid candidate.
  await removeDeveloperHubPatchStateFromIndex(env);
}
'''

if "// DEVELOPER_HUB_REVIEW_TREE_FIX_V1" not in text:
    if text.count(helper_anchor) != 1:
        raise SystemExit(f"ERROR: helper anchor count={text.count(helper_anchor)}; refusing unsafe patch")
    text = text.replace(helper_anchor, helper_replacement, 1)

old_advanced = 'await stageReviewedPreviewFiles(preview.files || [], secureAuth.gitEnv);'
new_advanced = 'await stageReviewedCandidateTree(preview.candidateTree, secureAuth.gitEnv);'
old_legacy = 'await stageReviewedPreviewFiles(preview.files || [], securePushAuth.gitEnv);'
new_legacy = 'await stageReviewedCandidateTree(preview.candidateTree, securePushAuth.gitEnv);'

if old_advanced in text:
    if text.count(old_advanced) != 1:
        raise SystemExit(f"ERROR: advanced stage call count={text.count(old_advanced)}; refusing unsafe patch")
    text = text.replace(old_advanced, new_advanced, 1)
elif new_advanced not in text:
    raise SystemExit("ERROR: advanced reviewed-stage call not found")

if old_legacy in text:
    if text.count(old_legacy) != 1:
        raise SystemExit(f"ERROR: legacy stage call count={text.count(old_legacy)}; refusing unsafe patch")
    text = text.replace(old_legacy, new_legacy, 1)
elif new_legacy not in text:
    raise SystemExit("ERROR: legacy reviewed-stage call not found")

# Safety assertions: keep the existing reviewed-tree equality guards and do not
# weaken preview fingerprint/security checks.
required_markers = [
    'if (stagedTree !== preview.candidateTree) throw new Error("Project files changed after review.");',
    'if (stagedTreeRaw.trim() !== preview.candidateTree)',
    'suppliedFingerprint !== preview.fingerprint',
    'previewFingerprint !== preview.fingerprint',
    new_advanced,
    new_legacy,
]
for marker in required_markers:
    if marker not in text:
        raise SystemExit(f"ERROR: required safety marker missing after patch: {marker}")

TARGET.write_text(text, encoding="utf-8")

print("PATCH=TCRM-DEVELOPER-HUB-REVIEW-TREE-FIX-V1")
print("ROOT_CAUSE_FIXED=REAL_INDEX_STALE_STATE_VS_FRESH_PREVIEW_INDEX")
print("ADVANCED_SYNC_STAGE=EXACT_REVIEWED_CANDIDATE_TREE")
print("LEGACY_PUSH_STAGE=EXACT_REVIEWED_CANDIDATE_TREE")
print("FINGERPRINT_GUARDS_PRESERVED=YES")
print("TREE_EQUALITY_GUARDS_PRESERVED=YES")
print("FILES_CHANGED=server/routes/developerHub.ts")
