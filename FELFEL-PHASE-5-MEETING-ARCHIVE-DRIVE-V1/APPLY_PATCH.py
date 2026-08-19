#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

PATCH_ID = "FELFEL-PHASE-5-MEETING-ARCHIVE-DRIVE-V1"
BASELINE_SHA = "cd70a4898ff2b2f11e8b7c5e7c7e476d04fe4a2c"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

NEW_SERVICE = "server/services/felfel/felfelMeetingArchiveService.ts"
NEW_TEST = "server/services/felfel/felfelMeetingArchiveService.test.ts"
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
        raise SystemExit(f"Refusing to overwrite existing Phase 5 file: {rel}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run this patch from the canonical TCRM repository root.")

head = run("git", "rev-parse", "HEAD")
if head != BASELINE_SHA:
    raise SystemExit(
        f"Baseline mismatch: {PATCH_ID} requires Phase 4 commit {BASELINE_SHA}, found {head}. "
        "Do not bypass this check."
    )

status_before = run("git", "status", "--short")
if status_before.strip():
    raise SystemExit(
        "Refusing to apply Phase 5 on a dirty working tree. Commit/review existing work first:\n"
        + status_before
    )

routers = load(ROUTERS)
page = load(PAGE)
phase4_required = [
    (routers, 'from "./services/felfel/felfelCrmActionService";', "Phase 4 CRM action import"),
    (routers, "createApprovedTasks: felfelProcedure", "Phase 4 task mutation"),
    (page, "CRM Context & Approved Actions", "Phase 4 CRM UI"),
    (page, "createApprovedTasksM", "Phase 4 task mutation UI"),
    (page, "crmClientId", "Phase 4 CRM client context"),
]
for source, marker, label in phase4_required:
    if marker not in source:
        raise SystemExit(f"Refusing to apply Phase 5: required {label} marker is missing: {marker}")

service_content = r'''import { createHash } from "node:crypto";
import { and, eq, isNull } from "drizzle-orm";
import { clients, deals } from "../../../drizzle/schema";
import { getDb } from "../../db";
import {
  buildProtectedCrmFileUrl,
  listCrmFiles,
  storeCrmFile,
} from "../crmFileStorage";
import {
  analyzeFelfelMeeting,
  type FelfelMeetingIntelligence,
} from "./felfelIntelligenceService";
import type { FelfelPlatform } from "./felfelAdapter";

const ARCHIVE_CATEGORY = "felfel_meeting_archive";
const ARCHIVE_FILE_CATEGORY = "meeting_intelligence_markdown";
const ARCHIVE_VERSION = "felfel-meeting-archive-v1";
const MAX_ARCHIVES_PER_CLIENT = 100;

function cleanInline(value: unknown, max = 2_000) {
  return String(value ?? "")
    .replace(/\u0000/g, "")
    .replace(/\r\n?/g, "\n")
    .trim()
    .slice(0, max);
}

export function escapeFelfelArchiveMarkdown(value: unknown, max = 12_000) {
  return cleanInline(value, max)
    .replace(/\\/g, "\\\\")
    .replace(/([`*_{}\[\]()#+\-.!|>])/g, "\\$1")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function listSection(title: string, values: string[]) {
  const valid = values.map((value) => escapeFelfelArchiveMarkdown(value, 2_000)).filter(Boolean);
  return [`## ${title}`, "", ...(valid.length ? valid.map((value) => `- ${value}`) : ["- —"]), ""].join("\n");
}

function personDateSuffix(owner?: string | null, dueDate?: string | null, labels?: { owner: string; due: string }) {
  const bits: string[] = [];
  if (owner) bits.push(`${labels?.owner || "Owner"}: ${escapeFelfelArchiveMarkdown(owner, 300)}`);
  if (dueDate) bits.push(`${labels?.due || "Due"}: ${escapeFelfelArchiveMarkdown(dueDate, 300)}`);
  return bits.length ? ` — ${bits.join(" | ")}` : "";
}

export function buildFelfelArchiveEntityKey(input: {
  platform: string;
  nativeId: string;
  language: "ar" | "en";
}) {
  return `felfel-meeting:${cleanInline(input.platform, 40)}:${cleanInline(input.nativeId, 255)}:${input.language}`;
}

export function buildFelfelArchiveMarker(input: {
  clientId: number;
  platform: string;
  nativeId: string;
  language: "ar" | "en";
}) {
  return createHash("sha256")
    .update(String(input.clientId))
    .update("\0")
    .update(String(input.platform))
    .update("\0")
    .update(String(input.nativeId))
    .update("\0")
    .update(input.language)
    .digest("hex")
    .slice(0, 24);
}

function safeFilenameToken(value: string, fallback: string) {
  const normalized = String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return normalized || fallback;
}

export function renderFelfelMeetingArchiveMarkdown(input: {
  intelligence: FelfelMeetingIntelligence;
  clientId: number;
  clientName: string;
  dealId?: number | null;
}) {
  const { intelligence } = input;
  const ar = intelligence.outputLanguage === "ar";
  const labels = ar
    ? {
        title: "أرشيف اجتماع فلفل",
        client: "العميل",
        deal: "الصفقة",
        meeting: "الاجتماع",
        generated: "وقت التحليل",
        summary: "الملخص",
        decisions: "القرارات",
        actions: "المهام",
        opinion: "رأي فلفل",
        recommendations: "التوصيات",
        risks: "المخاطر",
        opportunities: "الفرص",
        questions: "أسئلة المتابعة",
        owner: "المسؤول المذكور",
        due: "الموعد المذكور",
        priority: "الأولوية",
        warning: "تنبيه",
        truncated: "تم تجاوز حد تحليل النص في Phase 3؛ قد تكون بعض الأجزاء الوسطى غير ممثلة بالكامل.",
        privacy: "الخصوصية: هذا الملف يحتوي على نتائج التحليل المنظمة فقط ولا يحتوي على النص الكامل للتفريغ.",
      }
    : {
        title: "Felfel Meeting Archive",
        client: "Client",
        deal: "Deal",
        meeting: "Meeting",
        generated: "Analysis generated",
        summary: "Summary",
        decisions: "Decisions",
        actions: "Action Items",
        opinion: "Felfel's Take",
        recommendations: "Recommendations",
        risks: "Risks",
        opportunities: "Opportunities",
        questions: "Follow-up Questions",
        owner: "Mentioned owner",
        due: "Mentioned due date",
        priority: "Priority",
        warning: "Warning",
        truncated: "The Phase 3 transcript safety cap was reached; some middle transcript chunks may not be represented fully.",
        privacy: "Privacy: this archive stores structured intelligence only and does not store the raw meeting transcript.",
      };

  const lines: string[] = [
    `# ${labels.title}`,
    "",
    `- **${labels.client}:** ${escapeFelfelArchiveMarkdown(input.clientName, 255)} (#${Number(input.clientId)})`,
    `- **${labels.deal}:** ${input.dealId ? `#${Number(input.dealId)}` : "—"}`,
    `- **${labels.meeting}:** ${escapeFelfelArchiveMarkdown(intelligence.platform, 50)}/${escapeFelfelArchiveMarkdown(intelligence.nativeId, 255)}`,
    `- **${labels.generated}:** ${escapeFelfelArchiveMarkdown(intelligence.generatedAt, 100)}`,
    `- **Version:** ${ARCHIVE_VERSION}`,
    "",
    `> ${labels.privacy}`,
    "",
  ];

  if (intelligence.transcriptTruncated) {
    lines.push(`> **${labels.warning}:** ${labels.truncated}`, "");
  }

  lines.push(`## ${labels.summary}`, "", escapeFelfelArchiveMarkdown(intelligence.summary, 12_000) || "—", "");

  lines.push(`## ${labels.decisions}`, "");
  if (intelligence.decisions.length) {
    for (const item of intelligence.decisions) {
      lines.push(`- ${escapeFelfelArchiveMarkdown(item.decision, 2_000)}${personDateSuffix(item.owner, item.dueDate, { owner: labels.owner, due: labels.due })}`);
    }
  } else lines.push("- —");
  lines.push("");

  lines.push(`## ${labels.actions}`, "");
  if (intelligence.actionItems.length) {
    for (const item of intelligence.actionItems) {
      const suffix = personDateSuffix(item.owner, item.dueDate, { owner: labels.owner, due: labels.due });
      lines.push(`- ${escapeFelfelArchiveMarkdown(item.task, 2_000)}${suffix} — ${labels.priority}: ${escapeFelfelArchiveMarkdown(item.priority, 30)}`);
    }
  } else lines.push("- —");
  lines.push("");

  lines.push(`## ${labels.opinion}`, "", escapeFelfelArchiveMarkdown(intelligence.felfelOpinion.headline, 2_000) || "—", "");
  lines.push(listSection(labels.recommendations, intelligence.felfelOpinion.recommendations));
  lines.push(listSection(labels.risks, intelligence.felfelOpinion.risks));
  lines.push(listSection(labels.opportunities, intelligence.felfelOpinion.opportunities));
  lines.push(listSection(labels.questions, intelligence.felfelOpinion.followUpQuestions));

  lines.push(
    "---",
    "",
    `Felfel metadata: provider=${escapeFelfelArchiveMarkdown(intelligence.provider, 100)}, model=${escapeFelfelArchiveMarkdown(intelligence.model, 160)}, chunks=${Number(intelligence.chunksAnalyzed)}, transcriptSegments=${Number(intelligence.transcriptSegments)}, transcriptCharacters=${Number(intelligence.transcriptCharacters)}`,
    "",
  );

  return lines.join("\n").trim() + "\n";
}

async function requireCrmContext(clientId: number, dealId?: number | null) {
  const db = await getDb();
  if (!db) throw new Error("Database is not available");
  const clientRows = await db.select({
    id: clients.id,
    leadId: clients.leadId,
    dealId: clients.dealId,
    leadName: clients.leadName,
    contactEmail: clients.contactEmail,
    contactPhone: clients.contactPhone,
    phone: clients.phone,
  }).from(clients).where(and(eq(clients.id, clientId), isNull(clients.deletedAt))).limit(1);
  const client = clientRows[0];
  if (!client) throw new Error("Selected CRM client was not found or is inactive");

  if (dealId) {
    const dealRows = await db.select({ id: deals.id, leadId: deals.leadId }).from(deals)
      .where(and(eq(deals.id, dealId), isNull(deals.deletedAt))).limit(1);
    const deal = dealRows[0];
    if (!deal) throw new Error("Selected CRM deal was not found or is inactive");
    const directMatch = Number(client.dealId || 0) === Number(deal.id);
    const leadMatch = Number(client.leadId || 0) > 0 && Number(client.leadId) === Number(deal.leadId || 0);
    if (!directMatch && !leadMatch) throw new Error("Selected deal does not belong to the selected client");
  }

  const name = cleanInline(client.leadName, 255)
    || cleanInline(client.contactEmail, 320)
    || cleanInline(client.contactPhone || client.phone, 50)
    || `Client #${client.id}`;
  return { id: Number(client.id), name };
}

function toArchiveListItem(row: any) {
  return {
    id: Number(row.id),
    fileName: String(row.fileName || ""),
    description: row.description == null ? null : String(row.description),
    protectedUrl: buildProtectedCrmFileUrl(Number(row.id)),
    driveUrl: row.driveUrl == null ? null : String(row.driveUrl),
    driveUploadStatus: String(row.driveUploadStatus || "disabled"),
    createdAt: row.createdAt instanceof Date ? row.createdAt.toISOString() : String(row.createdAt || ""),
    entityKey: row.entityKey == null ? null : String(row.entityKey),
  };
}

export async function listFelfelMeetingArchives(clientId: number) {
  await requireCrmContext(clientId);
  const rows = await listCrmFiles({
    entityType: "client",
    entityId: clientId,
    includeDeleted: false,
    limit: MAX_ARCHIVES_PER_CLIENT,
  });
  return rows
    .filter((row: any) => String(row.category || "") === ARCHIVE_CATEGORY)
    .map(toArchiveListItem);
}

export async function archiveFelfelMeeting(input: {
  clientId: number;
  dealId?: number | null;
  platform: FelfelPlatform;
  nativeId: string;
  language?: "ar" | "en";
  actorUserId: number;
  confirm: boolean;
}) {
  if (input.confirm !== true) throw new Error("Explicit user confirmation is required before archiving a meeting");
  if (!Number.isInteger(input.clientId) || input.clientId <= 0) throw new Error("A valid CRM client is required");
  if (!Number.isInteger(input.actorUserId) || input.actorUserId <= 0) throw new Error("A valid acting user is required");

  const language = input.language || "ar";
  const client = await requireCrmContext(input.clientId, input.dealId);
  const entityKey = buildFelfelArchiveEntityKey({ platform: input.platform, nativeId: input.nativeId, language });
  const existingRows = await listCrmFiles({
    entityType: "client",
    entityId: input.clientId,
    entityKey,
    includeDeleted: false,
    limit: 10,
  });
  const existing = existingRows.find((row: any) => String(row.category || "") === ARCHIVE_CATEGORY);
  if (existing) {
    return {
      success: true,
      created: false,
      duplicate: true,
      archive: toArchiveListItem(existing),
    };
  }

  // Critical trust boundary: fetch/reuse Phase 3 intelligence server-side.
  // Never accept transcript or intelligence JSON from the browser for the archive payload.
  const intelligence = await analyzeFelfelMeeting({
    platform: input.platform,
    nativeId: cleanInline(input.nativeId, 255),
    language,
    force: false,
  });

  const markdown = renderFelfelMeetingArchiveMarkdown({
    intelligence,
    clientId: input.clientId,
    clientName: client.name,
    dealId: input.dealId,
  });
  const marker = buildFelfelArchiveMarker({
    clientId: input.clientId,
    platform: input.platform,
    nativeId: input.nativeId,
    language,
  });
  const fileName = `felfel-meeting-${safeFilenameToken(String(input.platform), "meeting")}-${safeFilenameToken(input.nativeId, "meeting")}-${language}.md`;
  const storageKey = `felfel/meeting-archives/client-${input.clientId}/${marker}/${fileName}`;
  const stored = await storeCrmFile({
    entityType: "client",
    entityId: input.clientId,
    entityKey,
    category: ARCHIVE_CATEGORY,
    fileCategory: ARCHIVE_FILE_CATEGORY,
    description: `Felfel meeting intelligence archive | meeting=${input.platform}/${input.nativeId} | deal=${input.dealId || "none"} | generatedAt=${intelligence.generatedAt}`,
    storageKey,
    fileName,
    buffer: Buffer.from(markdown, "utf8"),
    contentType: "text/markdown; charset=utf-8",
    uploadedBy: input.actorUserId,
    projectReferenceClientId: input.clientId,
  });

  return {
    success: true,
    created: true,
    duplicate: false,
    archive: {
      id: Number(stored.crmFileId || 0),
      fileName: stored.fileName,
      description: stored.description,
      protectedUrl: stored.protectedUrl,
      driveUrl: stored.driveUrl,
      driveUploadStatus: stored.driveUploadStatus,
      createdAt: intelligence.generatedAt,
      entityKey,
    },
  };
}
'''

test_content = r'''import { describe, expect, it } from "vitest";
import {
  buildFelfelArchiveEntityKey,
  buildFelfelArchiveMarker,
  escapeFelfelArchiveMarkdown,
  renderFelfelMeetingArchiveMarkdown,
} from "./felfelMeetingArchiveService";
import type { FelfelMeetingIntelligence } from "./felfelIntelligenceService";

function intelligence(overrides: Partial<FelfelMeetingIntelligence> = {}): FelfelMeetingIntelligence {
  return {
    version: "felfel-intelligence-v1",
    platform: "google_meet",
    nativeId: "abc-defg-hij",
    generatedAt: "2026-08-19T12:00:00.000Z",
    outputLanguage: "en",
    transcriptSegments: 12,
    transcriptCharacters: 3456,
    chunksAnalyzed: 1,
    transcriptTruncated: false,
    provider: "test-provider",
    model: "test-model",
    latencyMs: 10,
    cached: true,
    summary: "Customer wants the launch next week.",
    decisions: [{ decision: "Use option A", owner: "Sara", dueDate: "Thursday" }],
    actionItems: [{ task: "Send proposal", owner: "Omar", dueDate: "Tomorrow", priority: "high" }],
    felfelOpinion: {
      headline: "Good momentum",
      recommendations: ["Confirm scope"],
      risks: ["Timing is tight"],
      opportunities: ["Upsell analytics"],
      followUpQuestions: ["Who approves the budget?"],
    },
    ...overrides,
  };
}

describe("felfelMeetingArchiveService helpers", () => {
  it("builds a deterministic meeting archive key and client marker", () => {
    expect(buildFelfelArchiveEntityKey({ platform: "google_meet", nativeId: "abc-defg-hij", language: "en" }))
      .toBe("felfel-meeting:google_meet:abc-defg-hij:en");
    const first = buildFelfelArchiveMarker({ clientId: 7, platform: "google_meet", nativeId: "abc-defg-hij", language: "en" });
    const second = buildFelfelArchiveMarker({ clientId: 7, platform: "google_meet", nativeId: "abc-defg-hij", language: "en" });
    expect(first).toBe(second);
    expect(first).toMatch(/^[a-f0-9]{24}$/);
  });

  it("renders structured intelligence without embedding the raw transcript", () => {
    const markdown = renderFelfelMeetingArchiveMarkdown({
      intelligence: intelligence(),
      clientId: 7,
      clientName: "Acme",
      dealId: 21,
    });
    expect(markdown).toContain("# Felfel Meeting Archive");
    expect(markdown).toContain("## Summary");
    expect(markdown).toContain("## Decisions");
    expect(markdown).toContain("## Action Items");
    expect(markdown).toContain("## Felfel's Take");
    expect(markdown).toContain("does not store the raw meeting transcript");
    expect(markdown.toLowerCase()).not.toContain("transcript:");
  });

  it("adds a visible safety-cap warning when Phase 3 analysis was truncated", () => {
    const markdown = renderFelfelMeetingArchiveMarkdown({
      intelligence: intelligence({ transcriptTruncated: true }),
      clientId: 7,
      clientName: "Acme",
    });
    expect(markdown).toContain("transcript safety cap was reached");
  });

  it("escapes raw HTML and markdown control characters in archive content", () => {
    const escaped = escapeFelfelArchiveMarkdown('<script>alert(1)</script> [click](javascript:alert(1))');
    expect(escaped).not.toContain("<script>");
    expect(escaped).toContain("&lt;script&gt;");
    expect(escaped).toContain("\\[click\\]");
  });
});
'''

write_new(NEW_SERVICE, service_content)
write_new(NEW_TEST, test_content)

routers = load(ROUTERS)
import_anchor = '''import {
  createFelfelApprovedTasks,
  listFelfelCrmClients,
  listFelfelCrmDeals,
} from "./services/felfel/felfelCrmActionService";
'''
import_replacement = import_anchor + '''import {
  archiveFelfelMeeting,
  listFelfelMeetingArchives,
} from "./services/felfel/felfelMeetingArchiveService";
'''
if import_anchor not in routers:
    raise SystemExit("Refusing to patch server/routers.ts: Phase 4 CRM action import anchor not found.")
routers = routers.replace(import_anchor, import_replacement, 1)

list_anchor = '    listMeetings: felfelProcedure.query(() => listFelfelMeetings()),\n'
router_block = '''    listArchives: felfelProcedure
      .input(z.object({ clientId: z.number().int().positive() }).strict())
      .query(({ input }) => listFelfelMeetingArchives(input.clientId)),
    archiveMeeting: felfelProcedure
      .input(z.object({
        clientId: z.number().int().positive(),
        dealId: z.number().int().positive().optional().nullable(),
        platform: z.enum(["google_meet", "teams", "zoom", "jitsi"]),
        nativeId: z.string().trim().min(1).max(255),
        language: z.enum(["ar", "en"]).optional().default("ar"),
        confirm: z.literal(true),
      }).strict())
      .mutation(({ input, ctx }) => archiveFelfelMeeting({
        ...input,
        actorUserId: Number(ctx.user.id),
      })),
''' + list_anchor
if list_anchor not in routers:
    raise SystemExit("Refusing to patch server/routers.ts: Felfel listMeetings anchor not found.")
routers = routers.replace(list_anchor, router_block, 1)
(root / ROUTERS).write_text(routers, encoding="utf-8")

page = load(PAGE)
mutation_anchor = '''  const createApprovedTasksM = trpc.felfel.createApprovedTasks.useMutation({
    onSuccess: (data) => {
      toast.success(ar
        ? `تم إنشاء ${data.createdCount} مهمة${data.duplicateCount ? ` وتخطي ${data.duplicateCount} مكررة` : ""}`
        : `Created ${data.createdCount} task(s)${data.duplicateCount ? `; skipped ${data.duplicateCount} duplicate(s)` : ""}`);
      setSelectedActionItems({});
    },
    onError: (error) => toast.error(error.message),
  });

'''
mutation_replacement = mutation_anchor + '''  const archivesQ = trpc.felfel.listArchives.useQuery(
    { clientId: crmClientId || 1 },
    { enabled: Boolean(intelligence && crmClientId), refetchOnWindowFocus: false },
  );
  const archiveMeetingM = trpc.felfel.archiveMeeting.useMutation({
    onSuccess: (data) => {
      toast.success(data.duplicate
        ? (ar ? "أرشيف الاجتماع محفوظ بالفعل" : "Meeting archive already exists")
        : (ar ? "تم حفظ أرشيف الاجتماع في CRM وGoogle Drive" : "Meeting archive saved to CRM and Google Drive"));
      void utils.felfel.listArchives.invalidate({ clientId: crmClientId || 1 });
    },
    onError: (error) => toast.error(error.message),
  });

'''
if mutation_anchor not in page:
    raise SystemExit("Refusing to patch FelfelPage.tsx: Phase 4 approved tasks mutation anchor not found.")
page = page.replace(mutation_anchor, mutation_replacement, 1)

submit_anchor = '''  const selectedActionCount = Object.values(selectedActionItems).filter(Boolean).length;
  const submitApprovedActions = () => {
'''
archive_function = '''  const archiveCurrentMeeting = () => {
    if (!meeting || !intelligence || !crmClientId) return;
    archiveMeetingM.mutate({
      clientId: crmClientId,
      dealId: crmDealId,
      platform: meeting.platform as "google_meet" | "teams" | "zoom" | "jitsi",
      nativeId: meeting.nativeId,
      language: ar ? "ar" : "en",
      confirm: true,
    });
  };

''' + submit_anchor
if submit_anchor not in page:
    raise SystemExit("Refusing to patch FelfelPage.tsx: Phase 4 selectedActionCount anchor not found.")
page = page.replace(submit_anchor, archive_function, 1)

opinion_anchor = '                          <Card className="border-orange-500/30 bg-orange-500/5">\n'
archive_card = r'''                          <Card className="border-emerald-500/30 bg-emerald-500/5">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base">{ar ? "أرشيف الاجتماع وGoogle Drive" : "Meeting Archive & Google Drive"}</CardTitle>
                              <CardDescription>{ar ? "احفظ نسخة Markdown منظمة من تحليل فلفل داخل ملفات CRM وGoogle Drive. لا يتم حفظ النص الكامل للتفريغ." : "Save a structured Markdown copy of Felfel's intelligence into CRM Files and the existing Google Drive storage. The raw transcript is not archived."}</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              <div className="flex flex-wrap items-center gap-3">
                                <Button
                                  variant="outline"
                                  className="gap-2"
                                  disabled={!crmClientId || !meeting || !intelligence || archiveMeetingM.isPending}
                                  onClick={archiveCurrentMeeting}
                                >
                                  {archiveMeetingM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <ExternalLink className="h-4 w-4" />}
                                  {ar ? "حفظ الأرشيف في CRM + Drive" : "Save archive to CRM + Drive"}
                                </Button>
                                <span className="text-xs text-muted-foreground">{ar ? "يتطلب اختيار العميل. الصفقة اختيارية. الحفظ يدوي فقط ولن يحدث تلقائيًا بعد التحليل." : "A client must be selected; the deal is optional. Archiving is manual and never runs automatically after analysis."}</span>
                              </div>

                              {!crmClientId ? (
                                <p className="text-sm text-muted-foreground">{ar ? "اختر العميل أولًا من قسم ربط CRM أعلاه." : "Select the CRM client above before archiving."}</p>
                              ) : archivesQ.isLoading ? (
                                <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />{ar ? "جار تحميل الأرشيفات..." : "Loading archives..."}</div>
                              ) : archivesQ.error ? (
                                <p className="text-sm text-destructive">{archivesQ.error.message}</p>
                              ) : (archivesQ.data || []).length ? (
                                <div className="space-y-2">
                                  <p className="text-sm font-bold">{ar ? "الأرشيفات المحفوظة للعميل" : "Saved client meeting archives"}</p>
                                  {(archivesQ.data || []).slice(0, 8).map((archive: any) => (
                                    <div key={archive.id} className="flex flex-col gap-2 rounded-xl border bg-background/70 p-3 sm:flex-row sm:items-center sm:justify-between">
                                      <div className="min-w-0">
                                        <p className="truncate text-sm font-medium" dir="ltr">{archive.fileName}</p>
                                        <p className="text-xs text-muted-foreground">{formatTimestamp(archive.createdAt, ar)} • {archive.driveUploadStatus}</p>
                                      </div>
                                      <div className="flex gap-2">
                                        {archive.protectedUrl && <Button asChild size="sm" variant="ghost"><a href={archive.protectedUrl} target="_blank" rel="noreferrer">{ar ? "CRM" : "CRM"}</a></Button>}
                                        {archive.driveUrl && <Button asChild size="sm" variant="outline"><a href={archive.driveUrl} target="_blank" rel="noreferrer" className="gap-1"><ExternalLink className="h-3.5 w-3.5" />Drive</a></Button>}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-muted-foreground">{ar ? "لا توجد أرشيفات محفوظة لهذا العميل حتى الآن." : "No meeting archives have been saved for this client yet."}</p>
                              )}
                            </CardContent>
                          </Card>

''' + opinion_anchor
if opinion_anchor not in page:
    raise SystemExit("Refusing to patch FelfelPage.tsx: Felfel Opinion card anchor not found.")
page = page.replace(opinion_anchor, archive_card, 1)
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
print("Phase 5 scope:")
print("  - explicit manual meeting archive action")
print("  - archive linked to selected active CRM client and optional validated deal")
print("  - server-side Phase 3 intelligence is reused; browser transcript/intelligence JSON is not trusted")
print("  - structured Markdown archive contains summary, decisions, actions, Felfel opinion, risks/opportunities/follow-up questions")
print("  - raw transcript text is NOT archived")
print("  - existing TCRM storeCrmFile / Google Drive storage is reused")
print("  - CRM file row + Drive URL are returned/listed")
print("  - deterministic entity key prevents normal repeated-save duplicates")
print("")
print("No DB schema/migration, Vexa upstream, Evolution API, webhook, Tara implementation, Zaghloul, or Google Drive settings logic was modified.")
print("No real Google Meet E2E was run by this patch.")
print("No build, restart, commit, push, pull, fetch, reset, merge, rebase, migration, or cleanup was performed.")
print("Focused validation:")
print("  pnpm exec vitest run server/services/felfel/felfelAdapter.test.ts server/services/felfel/felfelIntelligenceService.test.ts server/services/felfel/felfelCrmActionService.test.ts server/services/felfel/felfelMeetingArchiveService.test.ts")
