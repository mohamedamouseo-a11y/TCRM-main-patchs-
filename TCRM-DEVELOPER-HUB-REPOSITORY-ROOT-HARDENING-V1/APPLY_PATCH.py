#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

BASELINE_SHA = "3d6a67c61dd0abce01d803469f81bcbf45c730a6"

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

targets = [
    "server/services/developerHubRepositoryRoot.ts",
    "server/services/developerHubGitHubRuntime.ts",
    "server/services/GitHubSyncService.ts",
    "server/routes/developerHub.ts",
    "server/services/developerHubRepositoryRoot.test.ts",
    "server/services/developerHubGitHubRuntime.test.ts",
]

def run(*args: str) -> str:
    result = subprocess.run(
        list(args),
        cwd=root,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"Command failed ({result.returncode}): {' '.join(args)}")
    return result.stdout.strip()

def load(rel: str) -> str:
    path = root / rel
    if not path.is_file():
        raise SystemExit(f"Missing required file: {rel}")
    return path.read_text(encoding="utf-8")

originals = {rel: load(rel) for rel in targets}
buffers = dict(originals)

def replace_once(rel: str, old: str, new: str) -> None:
    text = buffers[rel]
    if new in text:
        print(f"[already] {rel}")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"Refusing to patch {rel}: expected exactly one source anchor, found {count}."
        )
    buffers[rel] = text.replace(old, new, 1)
    print(f"[prepared] {rel}")

def write_prepared_changes() -> None:
    for rel in targets:
        if buffers[rel] != originals[rel]:
            (root / rel).write_text(buffers[rel], encoding="utf-8")

def rollback_prepared_changes() -> None:
    for rel in targets:
        if buffers[rel] != originals[rel]:
            (root / rel).write_text(originals[rel], encoding="utf-8")

package_path = root / "package.json"
if not package_path.is_file():
    raise SystemExit("Run this patch from the TCRM repository root.")
try:
    package_name = json.loads(package_path.read_text(encoding="utf-8")).get("name")
except Exception as exc:
    raise SystemExit(f"Cannot read package.json: {exc}")
if package_name != "tamiyouz_crm":
    raise SystemExit(
        f"Refusing to patch unexpected project package name: {package_name!r}"
    )

if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Target path is not the canonical Git repository root.")

head = run("git", "rev-parse", "HEAD")
if head != BASELINE_SHA:
    raise SystemExit(
        "Baseline mismatch. "
        f"Expected {BASELINE_SHA}, found {head}. "
        "Re-review the current Developer Hub files before applying this patch."
    )

status = run("git", "status", "--porcelain", "--", *targets)
if status:
    raise SystemExit(
        "Refusing to overwrite existing Developer Hub changes in patch target files:\n"
        + status
    )

replace_once(
    "server/services/developerHubRepositoryRoot.ts",
    '''function defaultGitTopLevel(candidate: string): string | null {
  try {
    const output = execFileSync("git", ["-C", candidate, "rev-parse", "--show-toplevel"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: 5_000,
      env: {
        PATH: process.env.PATH || "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        HOME: process.env.HOME || "/tmp",
        LC_ALL: "C",
        LANG: "C",
        GIT_CONFIG_NOSYSTEM: "1",
        GIT_TERMINAL_PROMPT: "0",
      },
    }).trim();
    return normalizeDirectory(output);
  } catch {
    return null;
  }
}
''',
    '''function gitProbeEnvironment(): NodeJS.ProcessEnv {
  return {
    PATH: process.env.PATH || "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    HOME: process.env.HOME || "/tmp",
    LC_ALL: "C",
    LANG: "C",
    GIT_CONFIG_NOSYSTEM: "1",
    GIT_CONFIG_SYSTEM: "/dev/null",
    GIT_CONFIG_GLOBAL: "/dev/null",
    GIT_TERMINAL_PROMPT: "0",
  };
}

function defaultGitTopLevel(candidate: string): string | null {
  try {
    const output = execFileSync("git", ["-C", candidate, "rev-parse", "--show-toplevel"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: 5_000,
      env: gitProbeEnvironment(),
    }).trim();
    return normalizeDirectory(output);
  } catch {
    return null;
  }
}

function defaultGitIsInsideWorkTree(candidate: string): boolean {
  try {
    return execFileSync("git", ["-C", candidate, "rev-parse", "--is-inside-work-tree"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: 5_000,
      env: gitProbeEnvironment(),
    }).trim() === "true";
  } catch {
    return false;
  }
}

export function assertCanonicalDeveloperHubGitRoot(candidate: string): string {
  const canonicalCandidate = normalizeDirectory(candidate);
  if (!canonicalCandidate) {
    throw new Error("Developer Hub repository path does not exist or is not a directory.");
  }
  if (!defaultGitIsInsideWorkTree(canonicalCandidate)) {
    throw new Error(
      "Developer Hub repository path is not inside a Git work tree. "
      + "Set DEV_HUB_REPO_DIR to the canonical TCRM repository root.",
    );
  }
  const gitRoot = defaultGitTopLevel(canonicalCandidate);
  if (!gitRoot) {
    throw new Error("Developer Hub could not resolve the Git work tree root.");
  }
  if (gitRoot !== canonicalCandidate) {
    throw new Error(
      `Developer Hub repository path must be the canonical Git work tree root (${gitRoot}).`,
    );
  }
  return gitRoot;
}
''',
)

replace_once(
    "server/services/developerHubRepositoryRoot.ts",
    '''  // Keep the application bootable when no repository is mounted. Git actions will
  // surface the existing clear "not a Git repository" error instead of crashing TCRM.
  const explicitNormalized = explicit ? normalizeDirectory(explicit) : null;
  if (explicitNormalized && readExpectedPackageName(explicitNormalized)) return explicitNormalized;
  const cwdNormalized = normalizeDirectory(cwd);
  if (cwdNormalized && readExpectedPackageName(cwdNormalized)) return cwdNormalized;
  return DEFAULT_REPOSITORY_ROOT;
''',
    '''  throw new Error(
    "Developer Hub repository root could not be resolved to a validated TCRM Git work tree. "
    + "Set DEV_HUB_REPO_DIR to the canonical repository root.",
  );
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.ts",
    '''import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
''',
    '''import { promisify } from "node:util";
import { assertCanonicalDeveloperHubGitRoot } from "./developerHubRepositoryRoot";

const execFileAsync = promisify(execFile);
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.ts",
    '''export async function assertSafeRepositoryGitConfiguration(repoDir: string): Promise<void> {
  const env: NodeJS.ProcessEnv = {
    ...buildProcessEnvironmentWithoutGitOverrides(),
    GIT_CONFIG_NOSYSTEM: "1",
    GIT_CONFIG_SYSTEM: "/dev/null",
    GIT_CONFIG_GLOBAL: "/dev/null",
  };
  const localKeys = await readRepositoryConfigKeys(repoDir, env, ["--local"]);
  const { stdout: worktreeConfigPathRaw } = await execFileAsync(
    "git",
    ["rev-parse", "--git-path", "config.worktree"],
    { cwd: repoDir, env, encoding: "utf8", maxBuffer: 1024 * 1024 },
  );
''',
    '''export async function assertSafeRepositoryGitConfiguration(repoDir: string): Promise<void> {
  // Fail closed at the Git safety boundary before any --local configuration read.
  // This produces a deterministic repository-resolution error instead of Git's
  // "fatal: --local can only be used inside a git repository" message.
  const canonicalRepoDir = assertCanonicalDeveloperHubGitRoot(repoDir);
  const env: NodeJS.ProcessEnv = {
    ...buildProcessEnvironmentWithoutGitOverrides(),
    GIT_CONFIG_NOSYSTEM: "1",
    GIT_CONFIG_SYSTEM: "/dev/null",
    GIT_CONFIG_GLOBAL: "/dev/null",
  };
  const localKeys = await readRepositoryConfigKeys(canonicalRepoDir, env, ["--local"]);
  const { stdout: worktreeConfigPathRaw } = await execFileAsync(
    "git",
    ["rev-parse", "--git-path", "config.worktree"],
    { cwd: canonicalRepoDir, env, encoding: "utf8", maxBuffer: 1024 * 1024 },
  );
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.ts",
    ''': path.resolve(repoDir, rawWorktreeConfigPath)
''',
    ''': path.resolve(canonicalRepoDir, rawWorktreeConfigPath)
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.ts",
    '''      worktreeKeys = await readRepositoryConfigKeys(repoDir, env, ["--file", worktreeConfigPath]);
''',
    '''      worktreeKeys = await readRepositoryConfigKeys(canonicalRepoDir, env, ["--file", worktreeConfigPath]);
''',
)

replace_once(
    "server/services/GitHubSyncService.ts",
    '''import { normalizeGitHubRepoUrl } from "./developerHubGitHubSecurity";

const execFileAsync = promisify(execFile);
''',
    '''import { normalizeGitHubRepoUrl } from "./developerHubGitHubSecurity";
import { resolveDeveloperHubRepositoryRoot } from "./developerHubRepositoryRoot";

const execFileAsync = promisify(execFile);
''',
)

replace_once(
    "server/services/GitHubSyncService.ts",
    '''function repoRoot() {
  return process.env.DEV_HUB_REPO_DIR || process.cwd();
}
''',
    '''function repoRoot() {
  return resolveDeveloperHubRepositoryRoot();
}
''',
)

replace_once(
    "server/routes/developerHub.ts",
    '''const REPO_DIR = resolveDeveloperHubRepositoryRoot();
const STORAGE_DIR = path.resolve(process.cwd(), "storage");
''',
    '''const repositoryResolution = (() => {
  try {
    return { root: resolveDeveloperHubRepositoryRoot(), error: null as Error | null };
  } catch (error) {
    return {
      root: "",
      error: error instanceof Error
        ? error
        : new Error("Developer Hub repository root could not be resolved."),
    };
  }
})();
const REPO_DIR = repositoryResolution.root;

function requireDeveloperHubRepositoryRoot(): string {
  if (REPO_DIR) return REPO_DIR;
  throw repositoryResolution.error
    || new Error("Developer Hub repository root could not be resolved.");
}

const STORAGE_DIR = path.resolve(process.cwd(), "storage");
''',
)

replace_once(
    "server/routes/developerHub.ts",
    '''  try {
    action = normalizeGitHubSyncAction(req.body?.action);
    await attachDeveloperHubOperationTracker({
      res,
      operationId,
      kind: "review",
''',
    '''  try {
    action = normalizeGitHubSyncAction(req.body?.action);
    requireDeveloperHubRepositoryRoot();
    await attachDeveloperHubOperationTracker({
      res,
      operationId,
      kind: "review",
''',
)

replace_once(
    "server/routes/developerHub.ts",
    '''  try {
    action = normalizeGitHubSyncAction(req.body?.action);
    await attachDeveloperHubOperationTracker({
      res,
      operationId: operationToken,
      kind: "execute",
''',
    '''  try {
    action = normalizeGitHubSyncAction(req.body?.action);
    requireDeveloperHubRepositoryRoot();
    await attachDeveloperHubOperationTracker({
      res,
      operationId: operationToken,
      kind: "execute",
''',
)

replace_once(
    "server/services/developerHubRepositoryRoot.test.ts",
    '''  it("does not run git init or mutate repositories", () => {
    const root = makeProject();
    const calls: string[] = [];
    resolveDeveloperHubRepositoryRoot({
      env: {},
      cwd: root,
      commonRoots: [],
      gitTopLevel: (candidate) => {
        calls.push(candidate);
        return root;
      },
    });
    expect(calls.length).toBeGreaterThan(0);
    expect(fs.existsSync(path.join(root, ".git"))).toBe(false);
  });
});
''',
    '''  it("does not run git init or mutate repositories", () => {
    const root = makeProject();
    const calls: string[] = [];
    resolveDeveloperHubRepositoryRoot({
      env: {},
      cwd: root,
      commonRoots: [],
      gitTopLevel: (candidate) => {
        calls.push(candidate);
        return root;
      },
    });
    expect(calls.length).toBeGreaterThan(0);
    expect(fs.existsSync(path.join(root, ".git"))).toBe(false);
  });

  it("fails closed instead of returning a non-Git fallback", () => {
    const root = makeProject();
    expect(() => resolveDeveloperHubRepositoryRoot({
      env: { DEV_HUB_REPO_DIR: root },
      cwd: root,
      argvEntry: path.join(root, "dist/index.js"),
      commonRoots: [],
      gitTopLevel: () => null,
    })).toThrow(/could not be resolved to a validated TCRM Git work tree/i);
  });
});
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.test.ts",
    '''describe("Developer Hub GitHub runtime safety", () => {
''',
    '''describe("Developer Hub GitHub runtime safety", () => {
  it("rejects a non-repository cwd before reading local Git configuration", async () => {
    const root = await fs.mkdtemp(path.join(os.tmpdir(), "tcrm-github-invalid-root-test-"));
    try {
      await expect(assertSafeRepositoryGitConfiguration(root))
        .rejects.toThrow(/not inside a Git work tree/i);
    } finally {
      await fs.rm(root, { recursive: true, force: true });
    }
  });

  it("rejects a nested directory instead of silently accepting a non-canonical Git cwd", async () => {
    const root = await fs.mkdtemp(path.join(os.tmpdir(), "tcrm-github-nested-root-test-"));
    const repo = path.join(root, "repo");
    const nested = path.join(repo, "nested");
    try {
      await execFileAsync("git", ["init", repo]);
      await fs.mkdir(nested);
      await expect(assertSafeRepositoryGitConfiguration(nested))
        .rejects.toThrow(/canonical Git work tree root/i);
    } finally {
      await fs.rm(root, { recursive: true, force: true });
    }
  });

''',
)

write_prepared_changes()
try:
    run("git", "diff", "--check", "--", *targets)
except BaseException:
    rollback_prepared_changes()
    raise

print("")
print("Developer Hub repository-root hardening patch applied.")
print(f"Baseline: {BASELINE_SHA}")
print("No commit, push, pull, merge, cleanup, restart, or deployment was performed.")
print("Run focused tests next:")
print(
    "  pnpm exec vitest run "
    "server/services/developerHubRepositoryRoot.test.ts "
    "server/services/developerHubGitHubRuntime.test.ts"
)
