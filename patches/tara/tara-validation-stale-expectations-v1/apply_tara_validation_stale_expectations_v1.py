#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

MARKER = "TCRM_TARA_VALIDATION_STALE_EXPECTATIONS_V1"
ROOT = Path.cwd()
PROVIDER_TEST = ROOT / "server/services/tara/taraProviderSecurity.test.ts"
SOCIAL_TEST = ROOT / "server/services/tara/taraSocialUnification.test.ts"

EXPECTED_PROVIDER_BLOB = "38b35e977bd72506b1f54118bbd099689e37f1f6"
EXPECTED_SOCIAL_BLOB = "1a6038ef9e89fbaa49423ed6197dabab0d7cd30e"


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def provider_target(source: str) -> str:
    source = source.replace(
        'baseUrl: "https://provider.example/v1",\n      provider: "openai_compatible",',
        'baseUrl: "https://api.openai.com/v1",\n      provider: "openai",',
    )
    source = source.replace(
        'expect(result.url.hostname).toBe("provider.example");',
        'expect(result.url.hostname).toBe("api.openai.com");',
    )
    return source


def social_target(source: str) -> str:
    old = 'expect(changedScope).not.toMatch(/rakanActionService|elevenLabsService|elevenlabs/i);'
    new = 'expect(changedScope).not.toMatch(/\\b(?:rakanActionService|elevenLabsService)\\b/i);'
    if old not in source:
        raise SystemExit("SOCIAL_EXPECTATION_PATTERN_NOT_FOUND")
    return source.replace(old, new)


def load_and_guard() -> tuple[str, str]:
    if not PROVIDER_TEST.exists() or not SOCIAL_TEST.exists():
        raise SystemExit("REQUIRED_TEST_FILE_MISSING")
    provider_blob = git_blob(PROVIDER_TEST)
    social_blob = git_blob(SOCIAL_TEST)
    if provider_blob != EXPECTED_PROVIDER_BLOB:
        raise SystemExit(f"PROVIDER_BASE_BLOB_MISMATCH={provider_blob}")
    if social_blob != EXPECTED_SOCIAL_BLOB:
        raise SystemExit(f"SOCIAL_BASE_BLOB_MISMATCH={social_blob}")
    return PROVIDER_TEST.read_text(encoding="utf-8"), SOCIAL_TEST.read_text(encoding="utf-8")


def targets() -> tuple[str, str]:
    provider, social = load_and_guard()
    p = provider_target(provider)
    s = social_target(social)
    if p == provider:
        raise SystemExit("PROVIDER_PATCH_NOOP")
    if s == social:
        raise SystemExit("SOCIAL_PATCH_NOOP")
    return p, s


def check() -> None:
    p, s = targets()
    print("CHECK=PASS")
    print(f"MARKER={MARKER}")
    print(f"PROVIDER_TARGET_SHA256={sha256_text(p)}")
    print(f"SOCIAL_TARGET_SHA256={sha256_text(s)}")


def apply() -> None:
    p, s = targets()
    PROVIDER_TEST.write_text(p, encoding="utf-8")
    SOCIAL_TEST.write_text(s, encoding="utf-8")
    print("APPLY=PASS")
    print(f"PROVIDER_NEW_BLOB={git_blob(PROVIDER_TEST)}")
    print(f"SOCIAL_NEW_BLOB={git_blob(SOCIAL_TEST)}")


def verify() -> None:
    provider = PROVIDER_TEST.read_text(encoding="utf-8")
    social = SOCIAL_TEST.read_text(encoding="utf-8")
    required_provider = [
        'baseUrl: "https://api.openai.com/v1"',
        'provider: "openai"',
        'expect(result.url.hostname).toBe("api.openai.com");',
    ]
    if not all(item in provider for item in required_provider):
        raise SystemExit("PROVIDER_VERIFY_FAILED")
    if 'provider: "openai_compatible"' in provider or 'provider.example' in provider:
        raise SystemExit("PROVIDER_STALE_PRECONDITION_REMAINS")
    expected_social = 'expect(changedScope).not.toMatch(/\\b(?:rakanActionService|elevenLabsService)\\b/i);'
    if expected_social not in social:
        raise SystemExit("SOCIAL_VERIFY_FAILED")
    if 'rakanActionService|elevenLabsService|elevenlabs' in social:
        raise SystemExit("SOCIAL_OVERBROAD_EXPECTATION_REMAINS")
    print("VERIFY=PASS")
    print(f"MARKER={MARKER}")
    print(f"PROVIDER_FINAL_BLOB={git_blob(PROVIDER_TEST)}")
    print(f"SOCIAL_FINAL_BLOB={git_blob(SOCIAL_TEST)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
    elif args.apply:
        apply()
    else:
        verify()


if __name__ == "__main__":
    main()
