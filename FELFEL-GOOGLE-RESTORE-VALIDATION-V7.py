#!/usr/bin/env python3
# FELFEL-GOOGLE-RESTORE-VALIDATION-V7
# Use Vexa's own restored-profile validation instead of custom ListAccounts parsing.
# Do not delete the uploaded session on a validation miss; fail closed and keep it for diagnosis.

from pathlib import Path
import os

target = Path("/var/www/TCRM-MAIN/ai-staff/felfel/deploy/compose/bin/felfel-auth-identity")
if not target.exists():
    raise SystemExit("PATCH_FAIL=IDENTITY_PROVISIONER_MISSING")

s = target.read_text(encoding="utf-8")

old = '''  let ok = false;
  try {
    const state = await rb.validateLoggedIn(page, "google");
    if (state.loggedIn) {
      const response = await context.request.get(
        "https://accounts.google.com/ListAccounts?gpsia=1&source=ChromiumBrowser&json=standard",
        { timeout: 30000 }
      );
      let body = await response.text();
      const firstArray = body.indexOf("[");
      if (firstArray > 0) body = body.slice(firstArray);
      const parsed = JSON.parse(body);
      const accounts = [];
      const walk = (value) => {
        if (!Array.isArray(value)) return;
        if (value[0] === "gaia.l.a" && String(value[3] || "").includes("@")) {
          accounts.push(value);
          return;
        }
        for (const child of value) walk(child);
      };
      walk(parsed);
      ok = accounts.length > 0;
    }
  } catch (_) {
    ok = false;
  }
  await context.close().catch(() => {});
  console.log("RESTORED_GOOGLE_AUTH=" + (ok ? "YES" : "NO"));
  process.exit(ok ? 0 : 42);'''

new = '''  let ok = false;
  let detail = "validation_failed";
  try {
    const state = await rb.validateLoggedIn(page, "google");
    ok = Boolean(state.loggedIn);
    detail = String(state.detail || "");
  } catch (error) {
    detail = String(error || "validation_error");
  }
  await context.close().catch(() => {});
  console.log("RESTORED_GOOGLE_AUTH=" + (ok ? "YES" : "NO") + " " + detail);
  process.exit(ok ? 0 : 42);'''

if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=V5_VALIDATION_ANCHOR_MISSING")
    s = s.replace(old, new, 1)

old_delete = '''  # Delete ONLY the invalid Felfel Google browser-data prefix.
  docker run --rm \
    --network "$NETWORK" \
    -e AWS_ACCESS_KEY_ID="$ACCESS" \
    -e AWS_SECRET_ACCESS_KEY="$SECRET" \
    -e ENDPOINT="$ENDPOINT" -e BUCKET="$BUCKET" -e PREFIX="$PREFIX" \
    --entrypoint sh "$BOT_IMAGE" -lc \
    'aws s3 rm "s3://${BUCKET}/${PREFIX}/browser-data" --recursive --endpoint-url "$ENDPOINT" >/dev/null 2>&1 || true' \
    >/dev/null 2>&1 || true
'''

if old_delete in s:
    s = s.replace(old_delete, '', 1)

target.write_text(s, encoding="utf-8")
os.chmod(target, 0o755)

print("PATCH=PASS")
print("GOOGLE_VALIDATION=VEXA_NATIVE_RESTORED_PROFILE")
print("INVALID_PROFILE_DELETE=DISABLED")
print("BUILD_REQUIRED=NO")
