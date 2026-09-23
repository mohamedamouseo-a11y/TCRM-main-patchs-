#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
WA = ROOT / "server/services/waGatewayIntegrationService.ts"
RUNNER = ROOT / "scripts/run-tdm-media-archive-v1.ts"
VERIFY = ROOT / "scripts/verify-tdm-media-archive-v1.ts"

for p in (WA, RUNNER, VERIFY):
    if not p.exists():
        raise SystemExit(f"ERROR=MISSING:{p}")

backup = ROOT / ".patch-backups" / f"tdm-media-evolution-recovery-v1-1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (WA, RUNNER, VERIFY):
    shutil.copy2(p, backup / p.name)

w = WA.read_text(encoding="utf-8")
start = w.find("export async function fetchWAGatewayHistoricalMediaBuffer(")
if start < 0:
    raise SystemExit("ERROR=HISTORICAL_MEDIA_FUNCTION_MISSING")
end = w.find("\nfunction remoteInstances(", start)
if end < 0:
    raise SystemExit("ERROR=HISTORICAL_MEDIA_FUNCTION_END_MISSING")

replacement = r'''export async function fetchWAGatewayHistoricalMediaBuffer(input: {
  sessionKey: string;
  rawMessage: unknown;
  messageId?: string | null;
  maxBytes?: number;
}) {
  const sessionKey = String(input.sessionKey || "").trim();
  if (!sessionKey) throw new Error("Evolution instance name is required");

  const parseMaybeJson = (value: unknown): any => {
    if (!value) return value;
    if (typeof value !== "string") return value;
    try { return JSON.parse(value); } catch { return value; }
  };

  const normalizeMessage = (value: unknown): any | null => {
    const root = parseMaybeJson(value);
    if (!root || typeof root !== "object" || Array.isArray(root)) return null;
    const key = parseMaybeJson((root as any).key);
    const message = parseMaybeJson((root as any).message);
    return {
      ...(root as any),
      ...(key && typeof key === "object" ? { key } : {}),
      ...(message && typeof message === "object" ? { message } : {}),
    };
  };

  const raw = normalizeMessage(input.rawMessage);
  const messageId = String(
    input.messageId ||
    raw?.key?.id ||
    raw?.id ||
    "",
  ).trim();
  if (!messageId) throw new Error("Evolution media message id is required");

  const maxBytes = Math.max(
    1024,
    Math.min(64 * 1024 * 1024, Math.floor(Number(input.maxBytes || 32 * 1024 * 1024))),
  );

  const candidates: any[] = [];
  const seen = new Set<string>();
  const addCandidate = (candidate: any) => {
    if (!candidate || typeof candidate !== "object") return;
    let signature = "";
    try { signature = JSON.stringify(candidate); } catch { return; }
    if (!signature || seen.has(signature)) return;
    seen.add(signature);
    candidates.push(candidate);
  };

  // Evolution's public contract accepts proto.WebMessageInfo. In current Evolution
  // versions a minimal key is enough for the Baileys service to resolve the stored message.
  addCandidate({
    key: {
      id: messageId,
      ...(raw?.key?.remoteJid ? { remoteJid: raw.key.remoteJid } : {}),
      ...(typeof raw?.key?.fromMe === "boolean" ? { fromMe: raw.key.fromMe } : {}),
      ...(raw?.key?.participant ? { participant: raw.key.participant } : {}),
    },
  });

  // Re-fetch the row by message id so recovery does not depend on a serialized
  // historical payload captured earlier by TDM.
  try {
    const fresh = await gatewayRequest(
      `/chat/findMessages/${encodeURIComponent(sessionKey)}`,
      {
        method: "POST",
        body: { where: { key: { id: messageId } }, page: 1, offset: 5 },
        strict: true,
        timeoutMs: 30_000,
        maxResponseBytes: 8 * 1024 * 1024,
      },
    );
    const freshRoot =
      fresh.response?.messages ??
      fresh.response?.data?.messages ??
      fresh.response?.data ??
      fresh.response ??
      {};
    const records = Array.isArray(freshRoot)
      ? freshRoot
      : Array.isArray(freshRoot?.records)
        ? freshRoot.records
        : [];
    for (const record of records) {
      const normalized = normalizeMessage(record);
      if (String(normalized?.key?.id || normalized?.id || "") === messageId) {
        addCandidate(normalized);
      }
    }
  } catch {
    // Stored TDM payload candidates below remain available.
  }

  if (raw) {
    addCandidate(raw);
    if (raw?.key && raw?.message) {
      addCandidate({
        key: raw.key,
        message: raw.message,
        ...(raw.messageType ? { messageType: raw.messageType } : {}),
        ...(raw.messageTimestamp ? { messageTimestamp: raw.messageTimestamp } : {}),
        ...(raw.pushName ? { pushName: raw.pushName } : {}),
      });
    }
  }

  if (!candidates.length) throw new Error("No Evolution media recovery candidates are available");

  const failures: string[] = [];
  for (let index = 0; index < candidates.length; index += 1) {
    try {
      const result = await gatewayRequest(
        `/chat/getBase64FromMediaMessage/${encodeURIComponent(sessionKey)}`,
        {
          method: "POST",
          strict: true,
          timeoutMs: 90_000,
          maxBodyBytes: 4 * 1024 * 1024,
          maxResponseBytes: Math.ceil(maxBytes * 1.5) + 2 * 1024 * 1024,
          body: { message: candidates[index], convertToMp4: false },
        },
      );

      const encoded = extractEvolutionBase64(result.response);
      if (!encoded) {
        failures.push(`candidate_${index + 1}:empty_base64`);
        continue;
      }
      const decoded = decodeWAGatewayBase64Media(encoded, maxBytes);
      if (!decoded?.length) {
        failures.push(`candidate_${index + 1}:decode_failed`);
        continue;
      }

      return {
        buffer: decoded,
        mimeType: String(
          result.response?.mimetype ||
          result.response?.mimeType ||
          result.response?.data?.mimetype ||
          result.response?.data?.mimeType ||
          "",
        ).trim() || null,
        recoveryCandidate: index + 1,
      };
    } catch (error: any) {
      failures.push(
        `candidate_${index + 1}:${String(error?.message || "request_failed")
          .replace(/[\r\n\t]+/g, " ")
          .slice(0, 160)}`,
      );
    }
  }

  throw new Error(
    `Evolution media recovery failed for ${messageId}: ${failures.join(" | ").slice(0, 700)}`,
  );
}
'''
w = w[:start] + replacement + w[end:]
WA.write_text(w, encoding="utf-8")

r = RUNNER.read_text(encoding="utf-8")
old = '''  const fetched = await fetchWAGatewayHistoricalMediaBuffer({
    sessionKey: job.sessionKey,
    rawMessage,
    maxBytes,
  });'''
new = '''  const fetched = await fetchWAGatewayHistoricalMediaBuffer({
    sessionKey: job.sessionKey,
    rawMessage,
    messageId: job.sourceMessageId,
    maxBytes,
  });'''
if old not in r:
    raise SystemExit("ERROR=RUNNER_FETCH_ANCHOR_MISSING")
r = r.replace(old, new, 1)
RUNNER.write_text(r, encoding="utf-8")

v = VERIFY.read_text(encoding="utf-8")
if 'EVOLUTION_KEY_LOOKUP' not in v:
    anchor = '''  console.log(`EVOLUTION_FALLBACK=${checks.EVOLUTION_FALLBACK ? "YES" : "NO"}`);'''
    repl = anchor + '''
  console.log(`EVOLUTION_KEY_LOOKUP=${wa.includes('where: { key: { id: messageId } }') ? "YES" : "NO"}`);
  console.log(`EVOLUTION_MINIMAL_KEY=${wa.includes('id: messageId') && wa.includes('getBase64FromMediaMessage') ? "YES" : "NO"}`);'''
    if anchor not in v:
        raise SystemExit("ERROR=VERIFY_ANCHOR_MISSING")
    v = v.replace(anchor, repl, 1)
    VERIFY.write_text(v, encoding="utf-8")

print("PATCH=PASS")
print("TDM_MEDIA_RECOVERY=V1_1")
print("EVOLUTION_MINIMAL_KEY=YES")
print("EVOLUTION_FRESH_LOOKUP=YES")
print("STORED_RAW_FALLBACK=YES")
print("SOURCE_WRITES=0")
print("RUNTIME_HOOK=NO")
print("FILES_CHANGED=3")
print(f"BACKUP={backup}")
print("ERROR=NONE")
