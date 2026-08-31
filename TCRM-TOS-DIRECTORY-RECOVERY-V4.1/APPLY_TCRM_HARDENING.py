#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
PATH = ROOT / "server/services/tosIntegrationService.ts"

if not PATH.exists():
    raise SystemExit(f"Missing expected file: {PATH}")

text = PATH.read_text(encoding="utf-8")

old = '''  if (!response.ok) {\n    const text = await response.text();\n    throw new Error(`Failed to fetch TOS team directory: ${response.status} ${text}`);\n  }\n  const body = await response.json();'''

new = '''  const responseText = await response.text();\n  const contentType = String(response.headers.get("content-type") || "").trim();\n  const responsePreview = responseText.trim().replace(/\\s+/g, " ").slice(0, 240);\n\n  if (!response.ok) {\n    throw new Error(\n      `Failed to fetch TOS team directory: ${response.status} ${contentType || "unknown-content-type"} ${responsePreview}`,\n    );\n  }\n\n  let body: any;\n  try {\n    body = responseText ? JSON.parse(responseText) : {};\n  } catch {\n    throw new Error(\n      `TOS team directory returned non-JSON content: ${response.status} ${contentType || "unknown-content-type"} ${responsePreview}`,\n    );\n  }'''

if new in text:
    print("[skip] TOS directory response parsing is already hardened")
elif old in text:
    PATH.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[ok] hardened {PATH}")
else:
    # Support production variants where the response.ok block already differs slightly.
    marker = '  const body = await response.json();'
    if marker not in text:
        raise SystemExit(
            "Could not find the expected response.json() anchor. Inspect the current getTosProjectTeamDirectory implementation and port the hardening manually."
        )
    replacement = '''  const responseText = await response.text();\n  const contentType = String(response.headers.get("content-type") || "").trim();\n  const responsePreview = responseText.trim().replace(/\\s+/g, " ").slice(0, 240);\n\n  if (!response.ok) {\n    throw new Error(\n      `Failed to fetch TOS team directory: ${response.status} ${contentType || "unknown-content-type"} ${responsePreview}`,\n    );\n  }\n\n  let body: any;\n  try {\n    body = responseText ? JSON.parse(responseText) : {};\n  } catch {\n    throw new Error(\n      `TOS team directory returned non-JSON content: ${response.status} ${contentType || "unknown-content-type"} ${responsePreview}`,\n    );\n  }'''
    # Do not blindly create a duplicate response.ok block if the current variant already consumes the body.
    before = text[: text.index(marker)]
    tail = before[-1200:]
    if "await response.text()" in tail:
        raise SystemExit(
            "Current code already consumes response.text() before response.json(); manual port required to avoid double-reading the response body."
        )
    PATH.write_text(text.replace(marker, replacement, 1), encoding="utf-8")
    print(f"[ok] hardened {PATH} using fallback anchor")

print("Review git diff and run npm run build before deployment.")
