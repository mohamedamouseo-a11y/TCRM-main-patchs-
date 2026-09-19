#!/usr/bin/env python3
from pathlib import Path

P=Path("/var/www/TCRM-MAIN/server/services/crmFileAuthorization.ts")
s=P.read_text(encoding="utf-8")

old='''  if (entityType === "deal") {
    const db = getPool();
    if (!db) return false;
    const [rows] = await db.execute<RowDataPacket[]>(`SELECT leadId FROM deals WHERE id = ? AND deletedAt IS NULL LIMIT 1`, [entityId]);
    const leadId = positiveInteger(rows[0]?.leadId);
    return leadId ? canReadLead(user, leadId) : false;
  }

  // No uploader or manager bypass for unknown active entity types.
  return role === "Admin" && entityType === "admin_private";'''

new='''  if (entityType === "deal") {
    const db = getPool();
    if (!db) return false;
    const [rows] = await db.execute<RowDataPacket[]>(`SELECT leadId FROM deals WHERE id = ? AND deletedAt IS NULL LIMIT 1`, [entityId]);
    const leadId = positiveInteger(rows[0]?.leadId);
    return leadId ? canReadLead(user, leadId) : false;
  }

  // FELFEL_RECORDING_AUTH_V1:
  // Felfel recordings are stored as general CRM files with a strict entityKey.
  // Permit Admin playback/download only when the embedded meeting id matches entityId.
  if (entityType === "general") {
    const key = String(file.entityKey ?? "").trim();
    const match = /^felfel:meeting:(\\d+):recording:(audio|video)$/.exec(key);
    if (match && Number(match[1]) === entityId) return role === "Admin";
  }

  // No uploader or manager bypass for unknown active entity types.
  return role === "Admin" && entityType === "admin_private";'''

if new in s:
    print("PATCH=PASS")
    print("ALREADY=YES")
    raise SystemExit(0)
if old not in s:
    print("PATCH=FAIL")
    print("ERROR=anchor_missing")
    raise SystemExit(1)

P.write_text(s.replace(old,new,1),encoding="utf-8")
print("PATCH=PASS")
print("FILES=1")
