#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

PATCH_ID = "FELFEL-PHASE-4-CRM-CONTEXT-ACTIONS-V1"
BASELINE_SHA = "c036cc68f85d76510d289b1c4060ef077f91e13d"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

NEW_SERVICE = "server/services/felfel/felfelCrmActionService.ts"
NEW_TEST = "server/services/felfel/felfelCrmActionService.test.ts"
ROUTERS = "server/routers.ts"
PAGE = "client/src/pages/FelfelPage.tsx"
TARGETS = [NEW_SERVICE, NEW_TEST, ROUTERS, PAGE]


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


def write_new(rel: str, content: str) -> None:
    path = root / rel
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing Phase 4 file: {rel}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run this patch from the canonical TCRM repository root.")

head = run("git", "rev-parse", "HEAD")
if head != BASELINE_SHA:
    raise SystemExit(
        f"Baseline mismatch: {PATCH_ID} requires Phase 3 commit {BASELINE_SHA}, found {head}. "
        "Do not bypass this check; confirm Phase 3 is the current clean baseline first."
    )

status_before = run("git", "status", "--short")
if status_before.strip():
    raise SystemExit(
        "Refusing to apply Phase 4 on a dirty working tree. Commit/push/review the existing work first:\n"
        + status_before
    )

routers = load(ROUTERS)
page = load(PAGE)
phase3_required = [
    (routers, 'import { analyzeFelfelMeeting } from "./services/felfel/felfelIntelligenceService";', "Phase 3 intelligence import"),
    (routers, "analyzeMeeting: felfelProcedure", "Phase 3 analyzeMeeting router"),
    (page, 'value="intelligence"', "Phase 3 intelligence tab"),
    (page, "Felfel Meeting Intelligence", "Phase 3 intelligence UI"),
    (page, "setIntelligence", "Phase 3 intelligence state"),
]
for source, marker, label in phase3_required:
    if marker not in source:
        raise SystemExit(f"Refusing to apply Phase 4: required {label} marker is missing: {marker}")

service_content = r'''import { createHash } from "node:crypto";
import { and, desc, eq, isNull, like, or } from "drizzle-orm";
import { clientTasks, clients, deals } from "../../../drizzle/schema";
import { createClientTask, getDb } from "../../db";

const MAX_CLIENT_RESULTS = 200;
const MAX_APPROVED_TASKS = 20;
const MAX_TASK_TITLE = 255;
const MAX_NOTES = 18_000;

export type FelfelCrmTaskPriority = "high" | "medium" | "low" | "unknown";

export interface FelfelApprovedActionInput {
  sourceIndex: number;
  title: string;
  priority?: FelfelCrmTaskPriority;
  aiOwner?: string | null;
  aiDueDate?: string | null;
}

export interface FelfelCrmClientOption {
  id: number;
  name: string;
  leadId: number | null;
  dealId: number | null;
  phone: string | null;
  email: string | null;
  accountManagerId: number | null;
}

export interface FelfelCrmDealOption {
  id: number;
  leadId: number | null;
  status: string;
  dealType: string | null;
  valueSar: string | null;
  currency: string;
}

async function dbOrThrow() {
  const db = await getDb();
  if (!db) throw new Error("Database is not available");
  return db;
}

function clampText(value: unknown, max: number) {
  return String(value ?? "").trim().slice(0, max);
}

function escapeLike(value: string) {
  return value.replace(/[\\%_]/g, (match) => `\\${match}`);
}

export function mapFelfelPriority(priority: FelfelCrmTaskPriority | undefined): "Low" | "Medium" | "High" {
  if (priority === "high") return "High";
  if (priority === "low") return "Low";
  return "Medium";
}

export function buildFelfelActionMarker(input: {
  platform: string;
  nativeId: string;
  clientId: number;
  dealId?: number | null;
  sourceIndex: number;
  title: string;
}) {
  const hash = createHash("sha256");
  hash.update(String(input.platform));
  hash.update("\0");
  hash.update(String(input.nativeId));
  hash.update("\0");
  hash.update(String(input.clientId));
  hash.update("\0");
  hash.update(String(input.dealId ?? ""));
  hash.update("\0");
  hash.update(String(input.sourceIndex));
  hash.update("\0");
  hash.update(clampText(input.title, 2_000));
  return hash.digest("hex").slice(0, 24);
}

export function buildFelfelTaskNotes(input: {
  marker: string;
  platform: string;
  nativeId: string;
  dealId?: number | null;
  originalTitle: string;
  aiOwner?: string | null;
  aiDueDate?: string | null;
  generatedAt?: string | null;
}) {
  const lines = [
    `[FELFEL_ACTION:${input.marker}]`,
    "Source: Felfel meeting intelligence — user-approved CRM task",
    `Meeting: ${clampText(input.platform, 32)}/${clampText(input.nativeId, 255)}`,
  ];
  if (input.dealId) lines.push(`Deal: #${Number(input.dealId)}`);
  if (input.generatedAt) lines.push(`Analysis generated at: ${clampText(input.generatedAt, 100)}`);
  if (input.aiOwner) lines.push(`Felfel suggested owner (not auto-assigned): ${clampText(input.aiOwner, 300)}`);
  if (input.aiDueDate) lines.push(`Felfel suggested due date (not auto-scheduled): ${clampText(input.aiDueDate, 300)}`);
  lines.push(`Action item: ${clampText(input.originalTitle, 2_000)}`);
  lines.push("Note: Felfel does not auto-assign owners or convert natural-language dates. Review this task in the normal CRM workflow.");
  return lines.join("\n").slice(0, MAX_NOTES);
}

export async function listFelfelCrmClients(input: { query?: string; limit?: number } = {}): Promise<FelfelCrmClientOption[]> {
  const db = await dbOrThrow();
  const limit = Math.max(1, Math.min(MAX_CLIENT_RESULTS, Number(input.limit || 100)));
  const query = clampText(input.query, 120);
  const fields = {
    id: clients.id,
    name: clients.leadName,
    leadId: clients.leadId,
    dealId: clients.dealId,
    phone: clients.phone,
    contactPhone: clients.contactPhone,
    email: clients.contactEmail,
    accountManagerId: clients.accountManagerId,
  };

  const rows = query
    ? await db.select(fields).from(clients).where(and(
        isNull(clients.deletedAt),
        or(
          like(clients.leadName, `%${escapeLike(query)}%`),
          like(clients.contactEmail, `%${escapeLike(query)}%`),
          like(clients.contactPhone, `%${escapeLike(query)}%`),
          like(clients.phone, `%${escapeLike(query)}%`),
        ),
      )).orderBy(desc(clients.updatedAt)).limit(limit)
    : await db.select(fields).from(clients).where(isNull(clients.deletedAt)).orderBy(desc(clients.updatedAt)).limit(limit);

  return rows.map((row: any) => ({
    id: Number(row.id),
    name: clampText(row.name, 255) || clampText(row.email, 320) || clampText(row.contactPhone || row.phone, 50) || `Client #${row.id}`,
    leadId: row.leadId == null ? null : Number(row.leadId),
    dealId: row.dealId == null ? null : Number(row.dealId),
    phone: clampText(row.contactPhone || row.phone, 50) || null,
    email: clampText(row.email, 320) || null,
    accountManagerId: row.accountManagerId == null ? null : Number(row.accountManagerId),
  }));
}

async function getActiveClient(clientId: number) {
  const db = await dbOrThrow();
  const rows = await db.select({
    id: clients.id,
    leadId: clients.leadId,
    dealId: clients.dealId,
    leadName: clients.leadName,
  }).from(clients).where(and(eq(clients.id, clientId), isNull(clients.deletedAt))).limit(1);
  if (!rows[0]) throw new Error("Selected CRM client was not found or is inactive");
  return rows[0];
}

export async function listFelfelCrmDeals(clientId: number): Promise<FelfelCrmDealOption[]> {
  const db = await dbOrThrow();
  const client = await getActiveClient(clientId);
  const leadId = client.leadId == null ? null : Number(client.leadId);
  const directDealId = client.dealId == null ? null : Number(client.dealId);
  if (!leadId && !directDealId) return [];

  const linkCondition = leadId && directDealId
    ? or(eq(deals.id, directDealId), eq(deals.leadId, leadId))
    : directDealId
      ? eq(deals.id, directDealId)
      : eq(deals.leadId, leadId!);

  const rows = await db.select({
    id: deals.id,
    leadId: deals.leadId,
    status: deals.status,
    dealType: deals.dealType,
    valueSar: deals.valueSar,
    currency: deals.currency,
  }).from(deals).where(and(isNull(deals.deletedAt), linkCondition)).orderBy(desc(deals.updatedAt)).limit(100);

  return rows.map((row: any) => ({
    id: Number(row.id),
    leadId: row.leadId == null ? null : Number(row.leadId),
    status: clampText(row.status, 50) || "Pending",
    dealType: clampText(row.dealType, 50) || null,
    valueSar: row.valueSar == null ? null : String(row.valueSar),
    currency: clampText(row.currency, 10) || "SAR",
  }));
}

async function assertDealBelongsToClient(client: any, dealId: number | null | undefined) {
  if (!dealId) return null;
  const db = await dbOrThrow();
  const rows = await db.select({ id: deals.id, leadId: deals.leadId }).from(deals)
    .where(and(eq(deals.id, dealId), isNull(deals.deletedAt))).limit(1);
  const deal = rows[0];
  if (!deal) throw new Error("Selected CRM deal was not found or is inactive");
  const directMatch = Number(client.dealId || 0) === Number(deal.id);
  const leadMatch = Number(client.leadId || 0) > 0 && Number(client.leadId) === Number(deal.leadId || 0);
  if (!directMatch && !leadMatch) throw new Error("Selected deal does not belong to the selected client");
  return Number(deal.id);
}

export async function createFelfelApprovedTasks(input: {
  clientId: number;
  dealId?: number | null;
  platform: string;
  nativeId: string;
  generatedAt?: string | null;
  tasks: FelfelApprovedActionInput[];
  actorUserId: number;
  confirm: boolean;
}) {
  if (input.confirm !== true) throw new Error("Explicit user confirmation is required before creating CRM tasks");
  if (!Number.isInteger(input.clientId) || input.clientId <= 0) throw new Error("A valid CRM client is required");
  if (!Number.isInteger(input.actorUserId) || input.actorUserId <= 0) throw new Error("A valid acting user is required");
  if (!Array.isArray(input.tasks) || input.tasks.length < 1 || input.tasks.length > MAX_APPROVED_TASKS) {
    throw new Error(`Select between 1 and ${MAX_APPROVED_TASKS} action items`);
  }

  const db = await dbOrThrow();
  const client = await getActiveClient(input.clientId);
  const dealId = await assertDealBelongsToClient(client, input.dealId);
  const created: Array<{ id: number; title: string; marker: string }> = [];
  const duplicates: Array<{ id: number | null; title: string; marker: string }> = [];

  for (const task of input.tasks) {
    const originalTitle = clampText(task.title, 2_000);
    if (!originalTitle) continue;
    const title = originalTitle.slice(0, MAX_TASK_TITLE);
    const marker = buildFelfelActionMarker({
      platform: input.platform,
      nativeId: input.nativeId,
      clientId: input.clientId,
      dealId,
      sourceIndex: Number(task.sourceIndex),
      title: originalTitle,
    });
    const markerText = `[FELFEL_ACTION:${marker}]`;
    const existing = await db.select({ id: clientTasks.id }).from(clientTasks).where(and(
      eq(clientTasks.clientId, input.clientId),
      isNull(clientTasks.deletedAt),
      like(clientTasks.notes, `%${markerText}%`),
    )).limit(1);
    if (existing[0]) {
      duplicates.push({ id: Number(existing[0].id), title, marker });
      continue;
    }

    const notes = buildFelfelTaskNotes({
      marker,
      platform: input.platform,
      nativeId: input.nativeId,
      dealId,
      originalTitle,
      aiOwner: task.aiOwner,
      aiDueDate: task.aiDueDate,
      generatedAt: input.generatedAt,
    });
    const id = Number(await createClientTask({
      clientId: input.clientId,
      title,
      priority: mapFelfelPriority(task.priority),
      status: "NotStarted",
      approvalStatus: "Pending",
      notes,
      createdBy: input.actorUserId,
    }));
    if (!id) throw new Error("CRM task creation failed");
    created.push({ id, title, marker });
  }

  if (!created.length && !duplicates.length) throw new Error("No valid action items were selected");
  return {
    success: true,
    clientId: input.clientId,
    dealId,
    created,
    duplicates,
    createdCount: created.length,
    duplicateCount: duplicates.length,
    approvalStatus: "Pending" as const,
    autoAssigned: false,
    autoScheduled: false,
  };
}
'''

test_content = r'''import { describe, expect, it } from "vitest";
import {
  buildFelfelActionMarker,
  buildFelfelTaskNotes,
  mapFelfelPriority,
} from "./felfelCrmActionService";

describe("felfelCrmActionService safety helpers", () => {
  it("maps Felfel priorities into existing CRM task priorities", () => {
    expect(mapFelfelPriority("high")).toBe("High");
    expect(mapFelfelPriority("medium")).toBe("Medium");
    expect(mapFelfelPriority("low")).toBe("Low");
    expect(mapFelfelPriority("unknown")).toBe("Medium");
  });

  it("builds deterministic per-client/per-meeting idempotency markers", () => {
    const base = {
      platform: "google_meet",
      nativeId: "abc-defg-hij",
      clientId: 42,
      dealId: 9,
      sourceIndex: 0,
      title: "Call the customer tomorrow",
    };
    const first = buildFelfelActionMarker(base);
    const second = buildFelfelActionMarker(base);
    const otherClient = buildFelfelActionMarker({ ...base, clientId: 43 });
    expect(first).toBe(second);
    expect(first).toMatch(/^[a-f0-9]{24}$/);
    expect(otherClient).not.toBe(first);
  });

  it("marks AI owner and date as suggestions rather than automatic assignments", () => {
    const notes = buildFelfelTaskNotes({
      marker: "1234567890abcdef12345678",
      platform: "google_meet",
      nativeId: "abc-defg-hij",
      dealId: 7,
      originalTitle: "Call the customer",
      aiOwner: "Ahmed",
      aiDueDate: "tomorrow at 10",
      generatedAt: "2026-08-19T10:00:00.000Z",
    });
    expect(notes).toContain("[FELFEL_ACTION:1234567890abcdef12345678]");
    expect(notes).toContain("not auto-assigned");
    expect(notes).toContain("not auto-scheduled");
    expect(notes).toContain("Deal: #7");
  });

  it("does not require or embed raw transcript content in CRM task metadata", () => {
    const notes = buildFelfelTaskNotes({
      marker: "abcdefabcdefabcdefabcdef",
      platform: "google_meet",
      nativeId: "abc-defg-hij",
      originalTitle: "Send proposal",
    });
    expect(notes).toContain("Action item: Send proposal");
    expect(notes.toLowerCase()).not.toContain("transcript:");
  });
});
'''

write_new(NEW_SERVICE, service_content)
write_new(NEW_TEST, test_content)

routers = load(ROUTERS)
import_anchor = 'import { analyzeFelfelMeeting } from "./services/felfel/felfelIntelligenceService";\n'
import_replacement = import_anchor + '''import {
  createFelfelApprovedTasks,
  listFelfelCrmClients,
  listFelfelCrmDeals,
} from "./services/felfel/felfelCrmActionService";
'''
if import_anchor not in routers:
    raise SystemExit("Refusing to patch server/routers.ts: Phase 3 Felfel intelligence import anchor not found.")
routers = routers.replace(import_anchor, import_replacement, 1)

list_anchor = '    listMeetings: felfelProcedure.query(() => listFelfelMeetings()),\n'
router_block = '''    crmClients: felfelProcedure
      .input(z.object({
        query: z.string().trim().max(120).optional().default(""),
        limit: z.number().int().min(1).max(200).optional().default(100),
      }).strict())
      .query(({ input }) => listFelfelCrmClients(input)),
    crmDeals: felfelProcedure
      .input(z.object({ clientId: z.number().int().positive() }).strict())
      .query(({ input }) => listFelfelCrmDeals(input.clientId)),
    createApprovedTasks: felfelProcedure
      .input(z.object({
        clientId: z.number().int().positive(),
        dealId: z.number().int().positive().optional().nullable(),
        platform: z.enum(["google_meet", "teams", "zoom", "jitsi"]),
        nativeId: z.string().trim().min(1).max(255),
        generatedAt: z.string().trim().max(100).optional().nullable(),
        confirm: z.literal(true),
        tasks: z.array(z.object({
          sourceIndex: z.number().int().min(0).max(1000),
          title: z.string().trim().min(1).max(2000),
          priority: z.enum(["high", "medium", "low", "unknown"]).optional().default("unknown"),
          aiOwner: z.string().trim().max(300).optional().nullable(),
          aiDueDate: z.string().trim().max(300).optional().nullable(),
        }).strict()).min(1).max(20),
      }).strict())
      .mutation(({ input, ctx }) => createFelfelApprovedTasks({
        ...input,
        actorUserId: Number(ctx.user.id),
      })),
''' + list_anchor
if list_anchor not in routers:
    raise SystemExit("Refusing to patch server/routers.ts: Felfel listMeetings anchor not found.")
routers = routers.replace(list_anchor, router_block, 1)
(root / ROUTERS).write_text(routers, encoding="utf-8")

page = load(PAGE)
state_anchor = '  const [intelligence, setIntelligence] = useState<any | null>(null);\n'
state_replacement = state_anchor + '''  const [crmClientSearch, setCrmClientSearch] = useState("");
  const [crmClientId, setCrmClientId] = useState<number | null>(null);
  const [crmDealId, setCrmDealId] = useState<number | null>(null);
  const [selectedActionItems, setSelectedActionItems] = useState<Record<number, boolean>>({});
'''
if state_anchor not in page:
    raise SystemExit("Refusing to patch FelfelPage.tsx: Phase 3 intelligence state anchor not found.")
page = page.replace(state_anchor, state_replacement, 1)

create_anchor = '  const createMeetingM = trpc.felfel.createMeeting.useMutation({\n'
crm_queries = '''  const crmClientsQ = trpc.felfel.crmClients.useQuery(
    { query: crmClientSearch.trim(), limit: 100 },
    { enabled: Boolean(intelligence), refetchOnWindowFocus: false },
  );
  const crmDealsQ = trpc.felfel.crmDeals.useQuery(
    { clientId: crmClientId || 1 },
    { enabled: Boolean(intelligence && crmClientId), refetchOnWindowFocus: false },
  );
  const createApprovedTasksM = trpc.felfel.createApprovedTasks.useMutation({
    onSuccess: (data) => {
      toast.success(ar
        ? `تم إنشاء ${data.createdCount} مهمة${data.duplicateCount ? ` وتخطي ${data.duplicateCount} مكررة` : ""}`
        : `Created ${data.createdCount} task(s)${data.duplicateCount ? `; skipped ${data.duplicateCount} duplicate(s)` : ""}`);
      setSelectedActionItems({});
    },
    onError: (error) => toast.error(error.message),
  });

''' + create_anchor
if create_anchor not in page:
    raise SystemExit("Refusing to patch FelfelPage.tsx: createMeeting mutation anchor not found.")
page = page.replace(create_anchor, crm_queries, 1)

# Reset CRM context whenever the selected meeting/intelligence is reset.
reset_old = '      setIntelligence(null);\n'
reset_new = '''      setIntelligence(null);
      setCrmClientId(null);
      setCrmDealId(null);
      setSelectedActionItems({});
'''
if reset_old not in page:
    raise SystemExit("Refusing to patch FelfelPage.tsx: intelligence reset anchor not found.")
page = page.replace(reset_old, reset_new)

analyze_success_old = '      setIntelligence(data);\n      toast.success(ar ? "فلفل خلّص تحليل الاجتماع" : "Felfel finished the meeting analysis");\n'
analyze_success_new = '''      setIntelligence(data);
      setSelectedActionItems({});
      toast.success(ar ? "فلفل خلّص تحليل الاجتماع" : "Felfel finished the meeting analysis");
'''
if analyze_success_old not in page:
    raise SystemExit("Refusing to patch FelfelPage.tsx: intelligence success anchor not found.")
page = page.replace(analyze_success_old, analyze_success_new, 1)

return_anchor = '  return (\n'
submit_block = '''  const selectedActionCount = Object.values(selectedActionItems).filter(Boolean).length;
  const submitApprovedActions = () => {
    if (!meeting || !intelligence || !crmClientId) return;
    const tasks = (intelligence.actionItems || []).flatMap((item: any, index: number) => selectedActionItems[index] ? [{
      sourceIndex: index,
      title: String(item.task || "").trim(),
      priority: (item.priority || "unknown") as "high" | "medium" | "low" | "unknown",
      aiOwner: item.owner || null,
      aiDueDate: item.dueDate || null,
    }] : []);
    if (!tasks.length) {
      toast.error(ar ? "اختر مهمة واحدة على الأقل" : "Select at least one action item");
      return;
    }
    createApprovedTasksM.mutate({
      clientId: crmClientId,
      dealId: crmDealId,
      platform: meeting.platform as "google_meet" | "teams" | "zoom" | "jitsi",
      nativeId: meeting.nativeId,
      generatedAt: intelligence.generatedAt || null,
      tasks,
      confirm: true,
    });
  };

''' + return_anchor
if return_anchor not in page:
    raise SystemExit("Refusing to patch FelfelPage.tsx: component return anchor not found.")
page = page.replace(return_anchor, submit_block, 1)

opinion_anchor = '                          <Card className="border-orange-500/30 bg-orange-500/5">\n'
crm_card = r'''                          <Card className="border-sky-500/30 bg-sky-500/5">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base">{ar ? "ربط CRM والمهام" : "CRM Context & Approved Actions"}</CardTitle>
                              <CardDescription>{ar ? "اختر العميل والصفقة يدويًا، ثم اختر المهام التي تريد إنشاؤها. فلفل لا يربط أو ينشئ أي شيء تلقائيًا." : "Manually choose the client and optional deal, then approve exactly which action items become CRM tasks. Felfel never auto-links or auto-creates tasks."}</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              <div className="grid gap-3 lg:grid-cols-2">
                                <div className="space-y-2">
                                  <Label htmlFor="felfel-client-search">{ar ? "بحث عن العميل" : "Find client"}</Label>
                                  <Input id="felfel-client-search" value={crmClientSearch} onChange={(event) => setCrmClientSearch(event.target.value)} placeholder={ar ? "الاسم أو البريد أو الهاتف" : "Name, email, or phone"} maxLength={120} />
                                  <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    value={crmClientId ?? ""}
                                    onChange={(event) => {
                                      const value = event.target.value ? Number(event.target.value) : null;
                                      setCrmClientId(value);
                                      setCrmDealId(null);
                                      setSelectedActionItems({});
                                    }}
                                  >
                                    <option value="">{ar ? "اختر العميل" : "Select client"}</option>
                                    {(crmClientsQ.data || []).map((client: any) => <option key={client.id} value={client.id}>{client.name}{client.phone ? ` — ${client.phone}` : client.email ? ` — ${client.email}` : ""}</option>)}
                                  </select>
                                  {crmClientsQ.isFetching && <p className="text-xs text-muted-foreground">{ar ? "جار البحث..." : "Searching clients..."}</p>}
                                </div>
                                <div className="space-y-2">
                                  <Label htmlFor="felfel-deal-select">{ar ? "الصفقة (اختياري)" : "Deal (optional)"}</Label>
                                  <select
                                    id="felfel-deal-select"
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    value={crmDealId ?? ""}
                                    disabled={!crmClientId || crmDealsQ.isFetching}
                                    onChange={(event) => setCrmDealId(event.target.value ? Number(event.target.value) : null)}
                                  >
                                    <option value="">{ar ? "بدون صفقة محددة" : "No specific deal"}</option>
                                    {(crmDealsQ.data || []).map((deal: any) => <option key={deal.id} value={deal.id}>#{deal.id} — {deal.dealType || "Deal"} — {deal.status}{deal.valueSar ? ` — ${deal.valueSar} ${deal.currency}` : ""}</option>)}
                                  </select>
                                  <p className="text-xs text-muted-foreground">{ar ? "لا يمكن اختيار صفقة لا تتبع العميل المحدد." : "The server rejects any deal that does not belong to the selected client."}</p>
                                </div>
                              </div>

                              <div className="space-y-2">
                                <p className="text-sm font-bold">{ar ? "اختر المهام المعتمدة" : "Choose approved action items"}</p>
                                {!intelligence.actionItems?.length ? <p className="text-sm text-muted-foreground">{ar ? "لا توجد Action Items في التحليل." : "No action items were found in the analysis."}</p> : intelligence.actionItems.map((item: any, index: number) => (
                                  <label key={index} className="flex cursor-pointer items-start gap-3 rounded-xl border bg-background/70 p-3">
                                    <input type="checkbox" className="mt-1 h-4 w-4" checked={Boolean(selectedActionItems[index])} onChange={(event) => setSelectedActionItems((current) => ({ ...current, [index]: event.target.checked }))} />
                                    <span className="min-w-0 flex-1">
                                      <span dir="auto" className="block text-sm font-medium">{item.task}</span>
                                      <span className="mt-1 block text-xs text-muted-foreground">{item.owner ? `${ar ? "اقتراح المسؤول" : "Suggested owner"}: ${item.owner}` : ar ? "بدون مسؤول محدد" : "No explicit owner"}{item.dueDate ? ` • ${ar ? "الموعد المذكور" : "Mentioned due date"}: ${item.dueDate}` : ""}</span>
                                    </span>
                                    <Badge variant="outline">{item.priority || "unknown"}</Badge>
                                  </label>
                                ))}
                              </div>

                              <div className="flex flex-wrap items-center gap-3 border-t pt-4">
                                <Button onClick={submitApprovedActions} disabled={!crmClientId || selectedActionCount < 1 || createApprovedTasksM.isPending} className="gap-2">
                                  {createApprovedTasksM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                                  {ar ? `إنشاء المهام المختارة (${selectedActionCount})` : `Create selected tasks (${selectedActionCount})`}
                                </Button>
                                <span className="text-xs text-muted-foreground">{ar ? "تُنشأ داخل CRM بحالة اعتماد Pending؛ اقتراحات المسؤول والموعد لا تُطبق تلقائيًا." : "Tasks are created in the CRM with Pending approval; suggested owners and natural-language dates are not auto-applied."}</span>
                              </div>
                            </CardContent>
                          </Card>

''' + opinion_anchor
if opinion_anchor not in page:
    raise SystemExit("Refusing to patch FelfelPage.tsx: unique Felfel Opinion card anchor not found.")
page = page.replace(opinion_anchor, crm_card, 1)
(root / PAGE).write_text(page, encoding="utf-8")

run("git", "diff", "--check", "--", *TARGETS)

print("")
print(f"{PATCH_ID} applied.")
print("Created:")
print(f"  {NEW_SERVICE}")
print(f"  {NEW_TEST}")
print("Modified:")
print(f"  {ROUTERS}")
print(f"  {PAGE}")
print("")
print("Phase 4 scope:")
print("  - manual CRM client search/selection")
print("  - optional deal selection, server-validated as belonging to the client")
print("  - explicit checkbox approval for Felfel action items")
print("  - creates existing client_tasks through createClientTask")
print("  - created tasks remain approvalStatus=Pending")
print("  - Felfel owner/date suggestions are stored as notes only; no auto-assignment or auto-scheduling")
print("  - deterministic action markers prevent duplicate creation from repeated clicks")
print("")
print("No DB schema/migration, Vexa upstream, Evolution API, webhook, Tara implementation, Zaghloul, Google Drive, or TOS sync logic was modified.")
print("No build, restart, commit, push, pull, fetch, reset, merge, rebase, migration, or cleanup was performed.")
print("Run focused validation next:")
print("  pnpm exec vitest run server/services/felfel/felfelAdapter.test.ts server/services/felfel/felfelIntelligenceService.test.ts server/services/felfel/felfelCrmActionService.test.ts")
print("Then run the normal TCRM production build.")
