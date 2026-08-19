#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

PATCH_ID = "FELFEL-PHASE-6-FOLLOW-UP-CRM-MEMORY-V1"
BASELINE_SHA = "401b1d5780ebc1c9b557a2be5841ed9a88e16909"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

NEW_SERVICE = "server/services/felfel/felfelFollowUpService.ts"
NEW_TEST = "server/services/felfel/felfelFollowUpService.test.ts"
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
        raise SystemExit(f"Refusing to overwrite existing Phase 6 file: {rel}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run this patch from the canonical TCRM repository root.")

head = run("git", "rev-parse", "HEAD")
if head != BASELINE_SHA:
    raise SystemExit(
        f"Baseline mismatch: {PATCH_ID} requires Phase 5 final commit {BASELINE_SHA}, found {head}."
    )

status_before = run("git", "status", "--short")
if status_before.strip():
    raise SystemExit("Refusing to apply Phase 6 on a dirty worktree:\n" + status_before)

routers = load(ROUTERS)
page = load(PAGE)
required_phase5 = [
    (routers, "archiveMeeting: felfelProcedure", "Phase 5 archive router"),
    (routers, 'from "./services/felfel/felfelMeetingArchiveService";', "Phase 5 archive import"),
    (page, "Meeting Archive & Google Drive", "Phase 5 archive UI"),
    (page, "archiveMeetingM", "Phase 5 archive mutation"),
    (page, "CRM Context & Approved Actions", "Phase 4 CRM context"),
]
for source, marker, label in required_phase5:
    if marker not in source:
        raise SystemExit(f"Required {label} marker missing: {marker}")

service_content = r'''import { createHash } from "node:crypto";
import { and, desc, eq, isNull, like } from "drizzle-orm";
import { clients, deals, followUps } from "../../../drizzle/schema";
import { createFollowUp, getDb } from "../../db";
import type { FelfelPlatform } from "./felfelAdapter";

export const FELFEL_FOLLOW_UP_TYPES = ["Call", "Meeting", "WhatsApp", "Email"] as const;
export type FelfelFollowUpType = (typeof FELFEL_FOLLOW_UP_TYPES)[number];

const MAX_FOLLOW_UP_HORIZON_MS = 366 * 24 * 60 * 60 * 1000;
const FELFEL_FOLLOW_UP_PREFIX = "FELFEL_FOLLOWUP:";

function cleanText(value: unknown, max = 2_000) {
  return String(value ?? "")
    .replace(/\u0000/g, "")
    .replace(/\r\n?/g, "\n")
    .trim()
    .slice(0, max);
}

export function parseFelfelFollowUpDate(value: string, nowMs = Date.now()) {
  const text = cleanText(value, 100);
  const parsed = new Date(text);
  const time = parsed.getTime();
  if (!text || Number.isNaN(time)) throw new Error("A valid follow-up date/time is required");
  if (time <= nowMs + 60_000) throw new Error("Follow-up date/time must be in the future");
  if (time > nowMs + MAX_FOLLOW_UP_HORIZON_MS) throw new Error("Follow-up date/time must be within the next 366 days");
  return parsed;
}

export function buildFelfelFollowUpMarker(input: {
  clientId: number;
  platform: string;
  nativeId: string;
  type: FelfelFollowUpType;
  followUpAt: string;
  topic?: string | null;
}) {
  const canonicalDate = new Date(input.followUpAt).toISOString();
  return `${FELFEL_FOLLOW_UP_PREFIX}${createHash("sha256")
    .update(String(input.clientId))
    .update("\0")
    .update(cleanText(input.platform, 50))
    .update("\0")
    .update(cleanText(input.nativeId, 255))
    .update("\0")
    .update(input.type)
    .update("\0")
    .update(canonicalDate)
    .update("\0")
    .update(cleanText(input.topic, 2_000))
    .digest("hex")
    .slice(0, 24)}`;
}

export function buildFelfelFollowUpNotes(input: {
  marker: string;
  platform: string;
  nativeId: string;
  dealId?: number | null;
  topic?: string | null;
}) {
  const topic = cleanText(input.topic, 2_000);
  const lines = [
    input.marker,
    `Source: Felfel meeting ${cleanText(input.platform, 50)}/${cleanText(input.nativeId, 255)}`,
    `Deal: ${input.dealId ? `#${Number(input.dealId)}` : "none"}`,
    "Scheduling source: explicit human-selected date/time; no AI date parsing was used.",
  ];
  if (topic) lines.push(`User-approved follow-up topic: ${topic}`);
  lines.push("Privacy: raw meeting transcript is not stored in this follow-up.");
  return lines.join("\n");
}

async function requireCrmContext(clientId: number, dealId?: number | null) {
  const db = await getDb();
  if (!db) throw new Error("Database is not available");
  const clientRows = await db.select({
    id: clients.id,
    leadId: clients.leadId,
    dealId: clients.dealId,
  }).from(clients)
    .where(and(eq(clients.id, clientId), isNull(clients.deletedAt)))
    .limit(1);
  const client = clientRows[0];
  if (!client) throw new Error("Selected CRM client was not found or is inactive");

  if (dealId) {
    const dealRows = await db.select({ id: deals.id, leadId: deals.leadId })
      .from(deals)
      .where(and(eq(deals.id, dealId), isNull(deals.deletedAt)))
      .limit(1);
    const deal = dealRows[0];
    if (!deal) throw new Error("Selected CRM deal was not found or is inactive");
    const directMatch = Number(client.dealId || 0) === Number(deal.id);
    const leadMatch = Number(client.leadId || 0) > 0 && Number(client.leadId) === Number(deal.leadId || 0);
    if (!directMatch && !leadMatch) throw new Error("Selected deal does not belong to the selected client");
  }
  return client;
}

function mapFollowUp(row: any) {
  return {
    id: Number(row.id),
    clientId: Number(row.clientId),
    userId: Number(row.userId),
    type: String(row.type || ""),
    followUpDate: row.followUpDate instanceof Date ? row.followUpDate.toISOString() : String(row.followUpDate || ""),
    notes: row.notes == null ? null : String(row.notes),
    status: String(row.status || "Pending"),
    createdAt: row.createdAt instanceof Date ? row.createdAt.toISOString() : String(row.createdAt || ""),
  };
}

export async function listFelfelCrmFollowUps(clientId: number) {
  await requireCrmContext(clientId);
  const db = await getDb();
  if (!db) throw new Error("Database is not available");
  const rows = await db.select().from(followUps)
    .where(and(
      eq(followUps.clientId, clientId),
      isNull(followUps.deletedAt),
      like(followUps.notes, `%${FELFEL_FOLLOW_UP_PREFIX}%`),
    ))
    .orderBy(desc(followUps.followUpDate))
    .limit(50);
  return rows.map(mapFollowUp);
}

export async function createFelfelCrmFollowUp(input: {
  clientId: number;
  dealId?: number | null;
  platform: FelfelPlatform;
  nativeId: string;
  type: FelfelFollowUpType;
  followUpAt: string;
  topic?: string | null;
  actorUserId: number;
  confirm: boolean;
}) {
  if (input.confirm !== true) throw new Error("Explicit confirmation is required before creating a follow-up");
  if (!Number.isInteger(input.clientId) || input.clientId <= 0) throw new Error("A valid CRM client is required");
  if (!Number.isInteger(input.actorUserId) || input.actorUserId <= 0) throw new Error("A valid acting user is required");
  if (!FELFEL_FOLLOW_UP_TYPES.includes(input.type)) throw new Error("Unsupported follow-up type");

  await requireCrmContext(input.clientId, input.dealId);
  const followUpDate = parseFelfelFollowUpDate(input.followUpAt);
  const marker = buildFelfelFollowUpMarker({
    clientId: input.clientId,
    platform: input.platform,
    nativeId: input.nativeId,
    type: input.type,
    followUpAt: followUpDate.toISOString(),
    topic: input.topic,
  });
  const notes = buildFelfelFollowUpNotes({
    marker,
    platform: input.platform,
    nativeId: input.nativeId,
    dealId: input.dealId,
    topic: input.topic,
  });

  const db = await getDb();
  if (!db) throw new Error("Database is not available");
  const existing = await db.select().from(followUps)
    .where(and(
      eq(followUps.clientId, input.clientId),
      isNull(followUps.deletedAt),
      like(followUps.notes, `%${marker}%`),
    ))
    .limit(1);
  if (existing[0]) {
    return { created: false, duplicate: true, followUp: mapFollowUp(existing[0]) };
  }

  // Reuse the existing CRM helper so normal follow-up behavior and client memory
  // fields remain owned by the CRM implementation, not by Felfel.
  await createFollowUp({
    clientId: input.clientId,
    userId: input.actorUserId,
    type: input.type,
    followUpDate,
    notes,
    status: "Pending",
  });

  const created = await db.select().from(followUps)
    .where(and(
      eq(followUps.clientId, input.clientId),
      isNull(followUps.deletedAt),
      like(followUps.notes, `%${marker}%`),
    ))
    .orderBy(desc(followUps.id))
    .limit(1);
  if (!created[0]) throw new Error("Follow-up was created but could not be reloaded");
  return { created: true, duplicate: false, followUp: mapFollowUp(created[0]) };
}
'''

test_content = r'''import { describe, expect, it } from "vitest";
import {
  buildFelfelFollowUpMarker,
  buildFelfelFollowUpNotes,
  parseFelfelFollowUpDate,
} from "./felfelFollowUpService";

describe("felfelFollowUpService safety helpers", () => {
  it("accepts an explicit future ISO date without interpreting natural-language AI dates", () => {
    const now = Date.parse("2026-08-19T10:00:00.000Z");
    const date = parseFelfelFollowUpDate("2026-08-20T11:30:00.000Z", now);
    expect(date.toISOString()).toBe("2026-08-20T11:30:00.000Z");
  });

  it("rejects past follow-up dates", () => {
    const now = Date.parse("2026-08-19T10:00:00.000Z");
    expect(() => parseFelfelFollowUpDate("2026-08-19T09:59:00.000Z", now)).toThrow(/future/i);
  });

  it("builds deterministic duplicate-protection markers", () => {
    const input = {
      clientId: 9,
      platform: "google_meet",
      nativeId: "abc-defg-hij",
      type: "Meeting" as const,
      followUpAt: "2026-08-20T11:30:00.000Z",
      topic: "Confirm final scope",
    };
    const first = buildFelfelFollowUpMarker(input);
    const second = buildFelfelFollowUpMarker(input);
    expect(first).toBe(second);
    expect(first).toMatch(/^FELFEL_FOLLOWUP:[a-f0-9]{24}$/);
  });

  it("stores only meeting provenance and the user-approved topic, not a raw transcript", () => {
    const notes = buildFelfelFollowUpNotes({
      marker: "FELFEL_FOLLOWUP:1234567890abcdef12345678",
      platform: "google_meet",
      nativeId: "abc-defg-hij",
      dealId: 12,
      topic: "Who approves the final budget?",
    });
    expect(notes).toContain("User-approved follow-up topic: Who approves the final budget?");
    expect(notes).toContain("no AI date parsing was used");
    expect(notes).toContain("raw meeting transcript is not stored");
    expect(notes.toLowerCase()).not.toContain("transcript:");
  });
});
'''

write_new(NEW_SERVICE, service_content)
write_new(NEW_TEST, test_content)

routers = load(ROUTERS)
import_anchor = '''import {
  archiveFelfelMeeting,
  listFelfelMeetingArchives,
} from "./services/felfel/felfelMeetingArchiveService";
'''
import_replacement = import_anchor + '''import {
  createFelfelCrmFollowUp,
  listFelfelCrmFollowUps,
} from "./services/felfel/felfelFollowUpService";
'''
if routers.count(import_anchor) != 1:
    raise SystemExit("Felfel archive import anchor not found exactly once in routers.ts")
routers = routers.replace(import_anchor, import_replacement, 1)

router_anchor = '''    listArchives: felfelProcedure
      .input(z.object({ clientId: z.number().int().positive() }).strict())
'''
router_insert = '''    crmFollowUps: felfelProcedure
      .input(z.object({ clientId: z.number().int().positive() }).strict())
      .query(({ input }) => listFelfelCrmFollowUps(input.clientId)),
    createFollowUp: felfelProcedure
      .input(z.object({
        clientId: z.number().int().positive(),
        dealId: z.number().int().positive().optional().nullable(),
        platform: z.enum(["google_meet", "teams", "zoom", "jitsi"]),
        nativeId: z.string().trim().min(1).max(255),
        type: z.enum(["Call", "Meeting", "WhatsApp", "Email"]),
        followUpAt: z.string().datetime({ offset: true }),
        topic: z.string().trim().max(2000).optional().nullable(),
        confirm: z.literal(true),
      }).strict())
      .mutation(({ input, ctx }) => createFelfelCrmFollowUp({
        ...input,
        actorUserId: Number(ctx.user.id),
      })),
''' + router_anchor
if routers.count(router_anchor) != 1:
    raise SystemExit("Felfel archive router anchor not found exactly once")
routers = routers.replace(router_anchor, router_insert, 1)
(root / ROUTERS).write_text(routers, encoding="utf-8")

page = load(PAGE)
state_anchor = '''  const [selectedActionItems, setSelectedActionItems] = useState<Record<number, boolean>>({});
'''
state_replacement = state_anchor + '''  const [followUpType, setFollowUpType] = useState<"Call" | "Meeting" | "WhatsApp" | "Email">("Call");
  const [followUpAt, setFollowUpAt] = useState("");
  const [followUpTopic, setFollowUpTopic] = useState("");
'''
if page.count(state_anchor) != 1:
    raise SystemExit("Felfel state anchor not found exactly once")
page = page.replace(state_anchor, state_replacement, 1)

mutation_anchor = '''  const archivesQ = trpc.felfel.listArchives.useQuery(
'''
mutation_insert = '''  const followUpsQ = trpc.felfel.crmFollowUps.useQuery(
    { clientId: crmClientId || 1 },
    { enabled: Boolean(intelligence && crmClientId), refetchOnWindowFocus: false },
  );
  const createFollowUpM = trpc.felfel.createFollowUp.useMutation({
    onSuccess: (data) => {
      toast.success(data.duplicate
        ? (ar ? "المتابعة محفوظة بالفعل" : "Follow-up already exists")
        : (ar ? "تم إنشاء المتابعة داخل CRM" : "CRM follow-up created"));
      void utils.felfel.crmFollowUps.invalidate({ clientId: crmClientId || 1 });
    },
    onError: (error) => toast.error(error.message),
  });

''' + mutation_anchor
if page.count(mutation_anchor) != 1:
    raise SystemExit("Felfel archive query anchor not found exactly once")
page = page.replace(mutation_anchor, mutation_insert, 1)

reset_anchor = '''      setSelectedActionItems({});
      setMeetingUrl(data.meetingUrl || meetingUrl);
'''
reset_replacement = '''      setSelectedActionItems({});
      setFollowUpAt("");
      setFollowUpTopic("");
      setMeetingUrl(data.meetingUrl || meetingUrl);
'''
if page.count(reset_anchor) != 1:
    raise SystemExit("Felfel createMeeting reset anchor not found exactly once")
page = page.replace(reset_anchor, reset_replacement, 1)

client_change_anchor = '''                                      setCrmDealId(null);
                                      setSelectedActionItems({});
'''
client_change_replacement = '''                                      setCrmDealId(null);
                                      setSelectedActionItems({});
                                      setFollowUpAt("");
                                      setFollowUpTopic("");
'''
if page.count(client_change_anchor) != 1:
    raise SystemExit("Felfel client-selection reset anchor not found exactly once")
page = page.replace(client_change_anchor, client_change_replacement, 1)

function_anchor = '''  const archiveCurrentMeeting = () => {
'''
function_insert = '''  const createCurrentFollowUp = () => {
    if (!meeting || !intelligence || !crmClientId) return;
    const parsed = new Date(followUpAt);
    if (!followUpAt || Number.isNaN(parsed.getTime())) {
      toast.error(ar ? "اختر تاريخ ووقت المتابعة" : "Choose a follow-up date and time");
      return;
    }
    if (parsed.getTime() <= Date.now() + 60_000) {
      toast.error(ar ? "موعد المتابعة لازم يكون في المستقبل" : "Follow-up must be scheduled in the future");
      return;
    }
    createFollowUpM.mutate({
      clientId: crmClientId,
      dealId: crmDealId,
      platform: meeting.platform as "google_meet" | "teams" | "zoom" | "jitsi",
      nativeId: meeting.nativeId,
      type: followUpType,
      followUpAt: parsed.toISOString(),
      topic: followUpTopic.trim() || null,
      confirm: true,
    });
  };

''' + function_anchor
if page.count(function_anchor) != 1:
    raise SystemExit("Felfel archive function anchor not found exactly once")
page = page.replace(function_anchor, function_insert, 1)

card_anchor = '''                          <Card className="border-emerald-500/30 bg-emerald-500/5">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base">{ar ? "أرشيف الاجتماع وGoogle Drive" : "Meeting Archive & Google Drive"}</CardTitle>
'''
followup_card = r'''                          <Card className="border-violet-500/30 bg-violet-500/5">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base">{ar ? "خطة المتابعة" : "Follow-up Planner"}</CardTitle>
                              <CardDescription>{ar ? "أنشئ متابعة CRM يدويًا من الاجتماع. أنت تختار نوع المتابعة والتاريخ والوقت؛ فلفل لا يحوّل مواعيد مكتوبة في الاجتماع إلى جدول تلقائي." : "Create a CRM follow-up manually from this meeting. You choose the channel and exact date/time; Felfel never converts natural-language dates into a schedule automatically."}</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              <div className="grid gap-3 lg:grid-cols-2">
                                <div className="space-y-2">
                                  <Label htmlFor="felfel-followup-type">{ar ? "نوع المتابعة" : "Follow-up type"}</Label>
                                  <select id="felfel-followup-type" className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={followUpType} onChange={(event) => setFollowUpType(event.target.value as typeof followUpType)}>
                                    <option value="Call">{ar ? "مكالمة" : "Call"}</option>
                                    <option value="Meeting">{ar ? "اجتماع" : "Meeting"}</option>
                                    <option value="WhatsApp">WhatsApp</option>
                                    <option value="Email">Email</option>
                                  </select>
                                </div>
                                <div className="space-y-2">
                                  <Label htmlFor="felfel-followup-at">{ar ? "التاريخ والوقت" : "Date & time"}</Label>
                                  <Input id="felfel-followup-at" type="datetime-local" value={followUpAt} onChange={(event) => setFollowUpAt(event.target.value)} />
                                  <p className="text-xs text-muted-foreground">{ar ? "الموعد ده اختيارك أنت؛ اقتراحات AI للمواعيد لا تُطبق تلقائيًا." : "This is your explicit schedule; AI-mentioned dates are never applied automatically."}</p>
                                </div>
                              </div>

                              <div className="space-y-2">
                                <Label htmlFor="felfel-followup-topic">{ar ? "موضوع المتابعة (اختياري)" : "Follow-up topic (optional)"}</Label>
                                <textarea id="felfel-followup-topic" className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={followUpTopic} maxLength={2000} onChange={(event) => setFollowUpTopic(event.target.value)} placeholder={ar ? "اكتب موضوع المتابعة أو اختر سؤالًا اقترحه فلفل بالأسفل" : "Write a topic or choose one of Felfel's suggested follow-up questions below"} />
                                {!!intelligence.felfelOpinion?.followUpQuestions?.length && (
                                  <div className="flex flex-wrap gap-2">
                                    {intelligence.felfelOpinion.followUpQuestions.slice(0, 8).map((question: string, index: number) => (
                                      <button key={index} type="button" onClick={() => setFollowUpTopic(question)} className="rounded-full border bg-background px-3 py-1.5 text-xs transition-colors hover:bg-muted" dir="auto">
                                        {question}
                                      </button>
                                    ))}
                                  </div>
                                )}
                              </div>

                              <div className="flex flex-wrap items-center gap-3 border-t pt-4">
                                <Button onClick={createCurrentFollowUp} disabled={!crmClientId || !meeting || !intelligence || !followUpAt || createFollowUpM.isPending} className="gap-2">
                                  {createFollowUpM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Clock3 className="h-4 w-4" />}
                                  {ar ? "إنشاء المتابعة" : "Create follow-up"}
                                </Button>
                                <span className="text-xs text-muted-foreground">{ar ? "المتابعة تُنشأ Pending ومسندة للمستخدم الذي أكدها؛ لا يوجد تعيين موظف أو جدولة تلقائية بواسطة AI." : "The follow-up is created Pending and assigned to the user who confirms it; there is no AI employee assignment or automatic scheduling."}</span>
                              </div>

                              {crmClientId && (
                                <div className="space-y-2">
                                  <p className="text-sm font-bold">{ar ? "متابعات فلفل لهذا العميل" : "Felfel follow-ups for this client"}</p>
                                  {followUpsQ.isLoading ? <div className="text-sm text-muted-foreground">{ar ? "جار التحميل..." : "Loading..."}</div> : followUpsQ.error ? <p className="text-sm text-destructive">{followUpsQ.error.message}</p> : !(followUpsQ.data || []).length ? <p className="text-sm text-muted-foreground">{ar ? "لا توجد متابعات أنشأها فلفل لهذا العميل." : "No Felfel follow-ups for this client yet."}</p> : (
                                    <div className="space-y-2">
                                      {(followUpsQ.data || []).slice(0, 8).map((item: any) => (
                                        <div key={item.id} className="flex flex-col gap-1 rounded-xl border bg-background/70 p-3 sm:flex-row sm:items-center sm:justify-between">
                                          <div><p className="text-sm font-medium">{item.type}</p><p className="text-xs text-muted-foreground">{formatTimestamp(item.followUpDate, ar)} • {item.status}</p></div>
                                          <Badge variant="outline">#{item.id}</Badge>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              )}
                            </CardContent>
                          </Card>

''' + card_anchor
if page.count(card_anchor) != 1:
    raise SystemExit("Felfel archive card anchor not found exactly once")
page = page.replace(card_anchor, followup_card, 1)
(root / PAGE).write_text(page, encoding="utf-8")

run("git", "diff", "--check", "--", *TARGETS)

print(f"{PATCH_ID} applied.")
print("Created:")
print(f"  {NEW_SERVICE}")
print(f"  {NEW_TEST}")
print("Modified:")
print(f"  {ROUTERS}")
print(f"  {PAGE}")
print("Phase 6 scope:")
print("  - manual CRM follow-up planner using existing follow_ups table and createFollowUp helper")
print("  - explicit human-selected Call/Meeting/WhatsApp/Email and exact date/time")
print("  - optional user-approved topic, including a manually selected Felfel follow-up question")
print("  - selected client required; optional deal is validated against client")
print("  - follow-up assigned to the confirming user only; no AI employee assignment")
print("  - Pending status; deterministic FELFEL_FOLLOWUP marker prevents normal duplicate clicks")
print("  - Felfel follow-up list shown for the selected client")
print("  - raw transcript is not stored; natural-language AI dates are not parsed or scheduled")
print("No DB schema/migration, Google Drive settings, Vexa, Evolution, Tara, Zaghloul, TOS, or webhook logic was modified.")
print("No real CRM follow-up, Google Meet E2E, build, restart, commit, push, fetch, pull, reset, merge, rebase, migration, or cleanup was performed by this patch.")
print("Focused validation command:")
print("  pnpm exec vitest run server/services/felfel/felfelAdapter.test.ts server/services/felfel/felfelIntelligenceService.test.ts server/services/felfel/felfelCrmActionService.test.ts server/services/felfel/felfelMeetingArchiveService.test.ts server/services/felfel/felfelFollowUpService.test.ts")
