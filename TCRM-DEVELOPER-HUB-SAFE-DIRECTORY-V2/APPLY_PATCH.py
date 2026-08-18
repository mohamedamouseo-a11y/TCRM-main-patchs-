#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

BASELINE_SHA = "3d6a67c61dd0abce01d803469f81bcbf45c730a6"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

targets = [
    "server/services/developerHubRepositoryRoot.ts",
    "server/services/developerHubGitHubRuntime.ts",
    "server/routes/developerHub.ts",
    "server/services/developerHubRepositoryRoot.test.ts",
    "server/services/developerHubGitHubRuntime.test.ts",
]


def run(*args: str) -> str:
    result = subprocess.run(list(args), cwd=root, text=True, capture_output=True)
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


def replace_all(rel: str, old: str, new: str, minimum: int = 1) -> None:
    text = buffers[rel]
    if new in text and old not in text:
        print(f"[already] {rel}: {old}")
        return
    count = text.count(old)
    if count < minimum:
        raise SystemExit(
            f"Refusing to patch {rel}: expected at least {minimum} occurrences of {old!r}, found {count}."
        )
    buffers[rel] = text.replace(old, new)
    print(f"[prepared] {rel}: replaced {count} occurrence(s)")


def write_changes() -> None:
    for rel in targets:
        if buffers[rel] != originals[rel]:
            (root / rel).write_text(buffers[rel], encoding="utf-8")


def rollback() -> None:
    for rel in targets:
        if buffers[rel] != originals[rel]:
            (root / rel).write_text(originals[rel], encoding="utf-8")


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run this patch from the canonical TCRM Git repository root.")

head = run("git", "rev-parse", "HEAD")
if head != BASELINE_SHA:
    raise SystemExit(
        f"Baseline mismatch: expected {BASELINE_SHA}, found {head}. Re-review before applying V2."
    )

# V2 is intentionally a completion patch over the already-applied V1 hardening.
required_v1_markers = {
    "server/services/developerHubRepositoryRoot.ts": [
        "assertCanonicalDeveloperHubGitRoot",
        "Developer Hub repository root could not be resolved to a validated TCRM Git work tree",
    ],
    "server/services/developerHubGitHubRuntime.ts": [
        "assertCanonicalDeveloperHubGitRoot",
        "const canonicalRepoDir = assertCanonicalDeveloperHubGitRoot(repoDir);",
    ],
    "server/routes/developerHub.ts": [
        "requireDeveloperHubRepositoryRoot",
        "const repositoryResolution = (() => {",
    ],
}
for rel, markers in required_v1_markers.items():
    for marker in markers:
        if marker not in buffers[rel]:
            raise SystemExit(
                f"Required V1 hardening marker missing from {rel}: {marker}. Apply/review V1 first."
            )

replace_once(
    "server/services/developerHubRepositoryRoot.ts",
    '''function defaultGitTopLevel(candidate: string): string | null {
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
''',
    '''function defaultGitTopLevel(candidate: string): string | null {
  const normalizedCandidate = normalizeDirectory(candidate);
  if (!normalizedCandidate) return null;
  try {
    const output = execFileSync("git", [
      "-c", `safe.directory=${normalizedCandidate}`,
      "-C", normalizedCandidate,
      "rev-parse", "--show-toplevel",
    ], {
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
  const normalizedCandidate = normalizeDirectory(candidate);
  if (!normalizedCandidate) return false;
  try {
    return execFileSync("git", [
      "-c", `safe.directory=${normalizedCandidate}`,
      "-C", normalizedCandidate,
      "rev-parse", "--is-inside-work-tree",
    ], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: 5_000,
      env: gitProbeEnvironment(),
    }).trim() === "true";
  } catch {
    return false;
  }
}
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.ts",
    '''function buildRestrictedGitConfigEnvironment(hooksPath: string): NodeJS.ProcessEnv {
  const config: Array<[string, string]> = [
    ["core.hooksPath", hooksPath],
''',
    '''function buildRestrictedGitConfigEnvironment(
  hooksPath: string,
  safeDirectory?: string,
): NodeJS.ProcessEnv {
  const config: Array<[string, string]> = [
    ...(safeDirectory ? [["safe.directory", safeDirectory] as [string, string]] : []),
    ["core.hooksPath", hooksPath],
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.ts",
    '''  const { stdout } = await execFileAsync(
    "git",
    ["config", ...args, "--includes", "--null", "--name-only", "--list"],
    { cwd: repoDir, env, encoding: "utf8", maxBuffer: 4 * 1024 * 1024 },
  );
''',
    '''  const { stdout } = await execFileAsync(
    "git",
    [
      "-c", `safe.directory=${repoDir}`,
      "config", ...args, "--includes", "--null", "--name-only", "--list",
    ],
    { cwd: repoDir, env, encoding: "utf8", maxBuffer: 4 * 1024 * 1024 },
  );
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.ts",
    '''  const { stdout: worktreeConfigPathRaw } = await execFileAsync(
    "git",
    ["rev-parse", "--git-path", "config.worktree"],
    { cwd: canonicalRepoDir, env, encoding: "utf8", maxBuffer: 1024 * 1024 },
  );
''',
    '''  const { stdout: worktreeConfigPathRaw } = await execFileAsync(
    "git",
    [
      "-c", `safe.directory=${canonicalRepoDir}`,
      "rev-parse", "--git-path", "config.worktree",
    ],
    { cwd: canonicalRepoDir, env, encoding: "utf8", maxBuffer: 1024 * 1024 },
  );
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.ts",
    '''async function createGitSandbox(prefix: string): Promise<{
  tempDir: string;
  hooksPath: string;
  gitEnv: NodeJS.ProcessEnv;
  cleanup: () => Promise<void>;
}> {
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), prefix));
''',
    '''async function createGitSandbox(prefix: string, repoDir?: string): Promise<{
  tempDir: string;
  hooksPath: string;
  gitEnv: NodeJS.ProcessEnv;
  cleanup: () => Promise<void>;
}> {
  const safeDirectory = repoDir ? assertCanonicalDeveloperHubGitRoot(repoDir) : undefined;
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), prefix));
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.ts",
    '''      gitEnv: buildRestrictedGitConfigEnvironment(hooksPath),
''',
    '''      gitEnv: buildRestrictedGitConfigEnvironment(hooksPath, safeDirectory),
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.ts",
    '''export async function createSafeGitEnvironment(): Promise<SafeGitEnvironment> {
  const sandbox = await createGitSandbox("tcrm-git-safe-");
  return { gitEnv: sandbox.gitEnv, cleanup: sandbox.cleanup };
}

export async function createSecureGitEnvironment(token: string): Promise<SecureGitEnvironment> {
  const sandbox = await createGitSandbox("tcrm-github-auth-");
''',
    '''export async function createSafeGitEnvironment(repoDir?: string): Promise<SafeGitEnvironment> {
  const sandbox = await createGitSandbox("tcrm-git-safe-", repoDir);
  return { gitEnv: sandbox.gitEnv, cleanup: sandbox.cleanup };
}

export async function createSecureGitEnvironment(
  token: string,
  repoDir?: string,
): Promise<SecureGitEnvironment> {
  const sandbox = await createGitSandbox("tcrm-github-auth-", repoDir);
''',
)

# Every Developer Hub route sandbox now receives the already-resolved canonical root,
# so all subsequent Git commands inherit a command-scoped safe.directory value even
# while global/system Git configuration remains disabled.
replace_all(
    "server/routes/developerHub.ts",
    "createSafeGitEnvironment()",
    "createSafeGitEnvironment(REPO_DIR)",
    minimum=1,
)
replace_all(
    "server/routes/developerHub.ts",
    "createSecureGitEnvironment(token)",
    "createSecureGitEnvironment(token, REPO_DIR)",
    minimum=1,
)
replace_all(
    "server/routes/developerHub.ts",
    "createSecureGitEnvironment(tokenToUse)",
    "createSecureGitEnvironment(tokenToUse, REPO_DIR)",
    minimum=1,
)
replace_all(
    "server/routes/developerHub.ts",
    'createSecureGitEnvironment("status-only")',
    'createSecureGitEnvironment("status-only", REPO_DIR)',
    minimum=1,
)
replace_all(
    "server/routes/developerHub.ts",
    'createSecureGitEnvironment("status-snapshot")',
    'createSecureGitEnvironment("status-snapshot", REPO_DIR)',
    minimum=1,
)

replace_once(
    "server/services/developerHubRepositoryRoot.test.ts",
    '''import { resolveDeveloperHubRepositoryRoot } from "./developerHubRepositoryRoot";
''',
    '''import {
  assertCanonicalDeveloperHubGitRoot,
  resolveDeveloperHubRepositoryRoot,
} from "./developerHubRepositoryRoot";
''',
)

replace_once(
    "server/services/developerHubRepositoryRoot.test.ts",
    '''  it("fails closed instead of returning a non-Git fallback", () => {
''',
    '''  it("accepts a canonical Git root while keeping the isolated probe policy", () => {
    const root = makeProject();
    subprocessGitInit(root);
    expect(assertCanonicalDeveloperHubGitRoot(root)).toBe(fs.realpathSync(root));
  });

  it("fails closed instead of returning a non-Git fallback", () => {
''',
)

# Add a tiny local helper without introducing a shell dependency.
replace_once(
    "server/services/developerHubRepositoryRoot.test.ts",
    '''function makeProject(name = "tamiyouz_crm") {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "tcrm-repo-root-"));
  tempRoots.push(root);
  fs.writeFileSync(path.join(root, "package.json"), JSON.stringify({ name }));
  return root;
}
''',
    '''function makeProject(name = "tamiyouz_crm") {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "tcrm-repo-root-"));
  tempRoots.push(root);
  fs.writeFileSync(path.join(root, "package.json"), JSON.stringify({ name }));
  return root;
}

function subprocessGitInit(root: string) {
  const result = require("node:child_process").spawnSync("git", ["init", root], {
    encoding: "utf8",
  });
  if (result.status !== 0) throw new Error(result.stderr || "git init failed");
}
''',
)

replace_once(
    "server/services/developerHubGitHubRuntime.test.ts",
    '''describe("Developer Hub GitHub runtime safety", () => {
''',
    '''describe("Developer Hub GitHub runtime safety", () => {
  it("injects only the canonical repository as sandbox safe.directory", async () => {
    const root = await fs.mkdtemp(path.join(os.tmpdir(), "tcrm-github-safe-directory-test-"));
    const repo = path.join(root, "repo");
    let safe: Awaited<ReturnType<typeof createSafeGitEnvironment>> | null = null;
    try {
      await execFileAsync("git", ["init", repo]);
      safe = await createSafeGitEnvironment(repo);
      const { stdout } = await execFileAsync(
        "git",
        ["config", "--get-all", "safe.directory"],
        { cwd: repo, env: safe.gitEnv, encoding: "utf8" },
      );
      expect(stdout.trim().split("\\n")).toContain(await fs.realpath(repo));
      expect(stdout).not.toContain("*\n");
    } finally {
      await safe?.cleanup();
      await fs.rm(root, { recursive: true, force: true });
    }
  });

''',
)

write_changes()
try:
    run("git", "diff", "--check", "--", *targets)
except BaseException:
    rollback()
    raise

print("")
print("Developer Hub command-scoped safe.directory V2 patch applied.")
print(f"HEAD baseline remains: {BASELINE_SHA}")
print("This patch does not persist safe.directory and does not modify Git configuration.")
print("No commit, push, pull, merge, cleanup, build, restart, or deployment was performed.")
print("Run focused tests:")
print(
    "  pnpm exec vitest run "
    "server/services/developerHubRepositoryRoot.test.ts "
    "server/services/developerHubGitHubRuntime.test.ts"
)
