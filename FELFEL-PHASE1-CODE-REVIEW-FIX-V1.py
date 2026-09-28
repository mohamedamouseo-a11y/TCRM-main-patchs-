#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path("/var/www/TCRM-MAIN")
EXPECTED_HEAD = "72290e529b766fe286443e748fd8acd50613ad79"
MARKER = "FELFEL_PHASE1_CODE_REVIEW_FIX_V1"

def fail(msg: str):
    print(f"PATCH=FAIL\nERROR={msg}")
    sys.exit(1)

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)

if not ROOT.exists():
    fail(f"root not found: {ROOT}")

head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
if head != EXPECTED_HEAD:
    fail(f"unexpected HEAD {head}; expected {EXPECTED_HEAD}")

calendar_path = ROOT / "server/googleCalendar.ts"
service_path = ROOT / "server/services/felfel/felfelCrmMeetingService.ts"
page_path = ROOT / "client/src/pages/FelfelPage.tsx"

for p in (calendar_path, service_path, page_path):
    if not p.exists():
        fail(f"missing file: {p}")

# ---------------------------------------------------------------------------
# 1) Google Calendar: poll the SAME event until Meet conference is ready.
# ---------------------------------------------------------------------------
calendar = calendar_path.read_text()

old_calendar = '''export async function createCalendarEvent(event: CalendarEvent): Promise<CalendarEventResult> {
  const calendar = await getCalendarClient();
  const description = [
    event.description || "",
    "",
    "─── CRM Details ───",
    event.leadId ? `Lead ID: ${event.leadId}` : "",
    event.clientId ? `Client ID: ${event.clientId}` : "",
    event.felfelMeetingId ? `Felfel Meeting ID: ${event.felfelMeetingId}` : "",
    event.leadName ? `Lead Name: ${event.leadName}` : "",
    event.agentName ? `Agent: ${event.agentName}` : "",
    "Created from Tamiyouz CRM",
  ].filter(Boolean).join("\\n");

  const metadata = privateMetadata(event);
  const eventBody: any = {
    summary: event.summary,
    description,
    location: event.location || undefined,
    start: { dateTime: event.startDateTime, timeZone: "Asia/Riyadh" },
    end: { dateTime: event.endDateTime, timeZone: "Asia/Riyadh" },
    reminders: {
      useDefault: false,
      overrides: [
        { method: "popup", minutes: 30 },
        { method: "popup", minutes: 10 },
      ],
    },
    ...(Object.keys(metadata).length ? { extendedProperties: { private: metadata } } : {}),
  };

  if (event.attendees && event.attendees.length > 0) {
    eventBody.description = (eventBody.description || "") + "\\n\\nAttendees: " + event.attendees.join(", ");
  }

  if (event.createGoogleMeet) {
    eventBody.conferenceData = {
      createRequest: {
        requestId: `tcrm-felfel-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
        conferenceSolutionKey: { type: "hangoutsMeet" },
      },
    };
  }

  const response = await calendar.events.insert({
    calendarId: CALENDAR_ID,
    requestBody: eventBody,
    ...(event.createGoogleMeet ? { conferenceDataVersion: 1 } : {}),
  });

  const result = toResult(response.data);
  if (event.createGoogleMeet && !result.meetingUrl) {
    throw new Error("Google Calendar created the event but did not return a Google Meet URL");
  }
  return result;
}

'''

new_calendar = '''// FELFEL_PHASE1_CODE_REVIEW_FIX_V1
function isGeneratedGoogleMeetUrl(value: unknown): value is string {
  if (typeof value !== "string") return false;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && url.hostname.toLowerCase() === "meet.google.com" && url.pathname.length > 1;
  } catch {
    return false;
  }
}

function conferenceStatus(data: any): string {
  return String(data?.conferenceData?.createRequest?.status?.statusCode || "").toLowerCase();
}

function conferenceError(message: string, calendarEventId?: string): Error & { calendarEventId?: string } {
  const error = new Error(message) as Error & { calendarEventId?: string };
  error.name = "CalendarConferenceCreationError";
  if (calendarEventId) error.calendarEventId = calendarEventId;
  return error;
}

export async function createCalendarEvent(event: CalendarEvent): Promise<CalendarEventResult> {
  const calendar = await getCalendarClient();
  const description = [
    event.description || "",
    "",
    "─── CRM Details ───",
    event.leadId ? `Lead ID: ${event.leadId}` : "",
    event.clientId ? `Client ID: ${event.clientId}` : "",
    event.felfelMeetingId ? `Felfel Meeting ID: ${event.felfelMeetingId}` : "",
    event.leadName ? `Lead Name: ${event.leadName}` : "",
    event.agentName ? `Agent: ${event.agentName}` : "",
    "Created from Tamiyouz CRM",
  ].filter(Boolean).join("\\n");

  const metadata = privateMetadata(event);
  const eventBody: any = {
    summary: event.summary,
    description,
    location: event.location || undefined,
    start: { dateTime: event.startDateTime, timeZone: "Asia/Riyadh" },
    end: { dateTime: event.endDateTime, timeZone: "Asia/Riyadh" },
    reminders: {
      useDefault: false,
      overrides: [
        { method: "popup", minutes: 30 },
        { method: "popup", minutes: 10 },
      ],
    },
    ...(Object.keys(metadata).length ? { extendedProperties: { private: metadata } } : {}),
  };

  if (event.attendees && event.attendees.length > 0) {
    eventBody.description = (eventBody.description || "") + "\\n\\nAttendees: " + event.attendees.join(", ");
  }

  if (event.createGoogleMeet) {
    eventBody.conferenceData = {
      createRequest: {
        requestId: `tcrm-felfel-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
        conferenceSolutionKey: { type: "hangoutsMeet" },
      },
    };
  }

  const response = await calendar.events.insert({
    calendarId: CALENDAR_ID,
    requestBody: eventBody,
    ...(event.createGoogleMeet ? { conferenceDataVersion: 1 } : {}),
  });

  let result = toResult(response.data);
  if (!event.createGoogleMeet) return result;

  const calendarEventId = String(response.data.id || result.id || "").trim() || undefined;
  if (isGeneratedGoogleMeetUrl(result.meetingUrl)) return result;
  if (!calendarEventId) {
    throw conferenceError("Google Calendar created an event without a usable event ID");
  }

  const initialStatus = conferenceStatus(response.data);
  if (initialStatus === "failure") {
    throw conferenceError("Google Meet conference creation failed", calendarEventId);
  }

  // Google conference creation is asynchronous. Poll the same event only;
  // never create a second event while waiting for the Meet URL.
  for (let attempt = 0; attempt < 12; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 1_000));
    const refreshed = await calendar.events.get({
      calendarId: CALENDAR_ID,
      eventId: calendarEventId,
      conferenceDataVersion: 1,
    });
    result = toResult(refreshed.data);
    if (isGeneratedGoogleMeetUrl(result.meetingUrl)) return result;

    const status = conferenceStatus(refreshed.data);
    if (status === "failure") {
      throw conferenceError("Google Meet conference creation failed", calendarEventId);
    }
  }

  throw conferenceError(
    "Timed out waiting for Google Meet conference URL",
    calendarEventId,
  );
}

'''

if MARKER not in calendar:
    calendar = replace_once(calendar, old_calendar, new_calendar, "googleCalendar createCalendarEvent")
    calendar_path.write_text(calendar)

# ---------------------------------------------------------------------------
# 2) CRM service: correct lead lookup + cleanup orphan calendar event.
# ---------------------------------------------------------------------------
service = service_path.read_text()

if MARKER not in service:
    service = replace_once(
        service,
        'import { clients, crmMeetings, deals } from "../../../drizzle/schema";',
        'import { clients, crmMeetings, deals, leads } from "../../../drizzle/schema";\nimport { createCalendarEvent, deleteCalendarEvent } from "../../googleCalendar"; // FELFEL_PHASE1_CODE_REVIEW_FIX_V1',
        "service imports",
    )

    old_lead = '''  } else if (input.leadId) {
    const lead = (await db.select({ name: clients.name }).from(clients)
      .innerJoin(deals, eq(deals.leadId, clients.leadId))
      .where(and(eq(deals.leadId, input.leadId), isNull(deals.deletedAt)))
      .limit(1))[0];
    if (lead?.name) contextName = lead.name;
  }
'''
    new_lead = '''  } else if (input.leadId) {
    const lead = (await db.select({ name: leads.name }).from(leads)
      .where(and(eq(leads.id, input.leadId), isNull(leads.deletedAt)))
      .limit(1))[0];
    if (lead?.name) contextName = lead.name;
  }
'''
    service = replace_once(service, old_lead, new_lead, "lead title lookup")

    old_calendar_call = '''  let calendarResult;
  try {
    const { createCalendarEvent } = await import("../../googleCalendar");
    calendarResult = await createCalendarEvent({
      summary: title,
      startDateTime,
      endDateTime,
      leadId: input.leadId ?? undefined,
      clientId: input.clientId ?? undefined,
      ownerUserId: input.ownerUserId,
      felfelMeetingId: crmMeetingId,
      createGoogleMeet: true,
    });
  } catch (err: any) {
    // Calendar/Meet creation failed — mark CRM record with error, do not leave fake URL
    await db.update(crmMeetings).set({
      status: "failed",
      lastError: err?.message || "Failed to create Google Calendar event with Meet link",
      auditData: jsonValue([{ event: "generated_meeting_calendar_failed", error: err?.message, at: new Date().toISOString() }]),
    }).where(eq(crmMeetings.id, crmMeetingId));
    throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: err?.message || "Failed to create Google Meet" });
  }

'''
    new_calendar_call = '''  let calendarResult;
  try {
    calendarResult = await createCalendarEvent({
      summary: title,
      startDateTime,
      endDateTime,
      leadId: input.leadId ?? undefined,
      clientId: input.clientId ?? undefined,
      ownerUserId: input.ownerUserId,
      felfelMeetingId: crmMeetingId,
      createGoogleMeet: true,
    });
  } catch (err: any) {
    const calendarEventId = typeof err?.calendarEventId === "string" ? err.calendarEventId : null;
    let cleanupError: string | null = null;
    if (calendarEventId) {
      try {
        await deleteCalendarEvent(calendarEventId);
      } catch (cleanupErr: any) {
        cleanupError = cleanupErr?.message || "Calendar cleanup failed";
      }
    }

    const errorMessage = err?.message || "Failed to create Google Calendar event with Meet link";
    await db.update(crmMeetings).set({
      status: "failed",
      lastError: cleanupError ? `${errorMessage}; cleanup: ${cleanupError}` : errorMessage,
      auditData: jsonValue([{
        event: "generated_meeting_calendar_failed",
        error: errorMessage,
        calendarEventId,
        orphanCleanupAttempted: Boolean(calendarEventId),
        orphanCleanupSucceeded: Boolean(calendarEventId) && !cleanupError,
        cleanupError,
        at: new Date().toISOString(),
      }]),
    }).where(eq(crmMeetings.id, crmMeetingId));
    throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: errorMessage });
  }

'''
    service = replace_once(service, old_calendar_call, new_calendar_call, "calendar cleanup path")
    service_path.write_text(service)

# ---------------------------------------------------------------------------
# 3) UI: client/deal selection must work before intelligence exists.
# ---------------------------------------------------------------------------
page = page_path.read_text()

if MARKER not in page:
    old_queries = '''  const crmClientsQ = trpc.felfel.crmClients.useQuery(
    { query: crmClientSearch.trim(), limit: 100 },
    { enabled: Boolean(intelligence), refetchOnWindowFocus: false },
  );
  const crmDealsQ = trpc.felfel.crmDeals.useQuery(
    { clientId: crmClientId || 1 },
    { enabled: Boolean(intelligence && crmClientId), refetchOnWindowFocus: false },
  );
'''
    new_queries = '''  // FELFEL_PHASE1_CODE_REVIEW_FIX_V1
  // Generated meetings need CRM context before a transcript/intelligence exists.
  const crmClientsQ = trpc.felfel.crmClients.useQuery(
    { query: crmClientSearch.trim(), limit: 100 },
    { enabled: isFelfelAdmin, refetchOnWindowFocus: false },
  );
  const crmDealsQ = trpc.felfel.crmDeals.useQuery(
    { clientId: crmClientId || 1 },
    { enabled: Boolean(isFelfelAdmin && crmClientId), refetchOnWindowFocus: false },
  );
'''
    page = replace_once(page, old_queries, new_queries, "page CRM query gating")

    old_block = '''                {/* FELFEL_PHASE1_GENERATED_MEETING_V1 */}
                <div className="border-t pt-3 mt-1">
                  <Button
                    onClick={() => generateMeetingM.mutate({
                      clientId: crmClientId ?? undefined,
                      leadId: undefined,
                      dealId: crmDealId ?? undefined,
                    })}
                    disabled={generateMeetingM.isPending || (!crmClientId && !crmDealId)}
                    className="h-11 w-full gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-400 font-bold text-white shadow-sm hover:from-emerald-700 hover:to-emerald-500"
                  >
                    {generateMeetingM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <VideoIcon className="h-4 w-4" />}
                    {ar ? "إنشاء اجتماع بفلفل" : "Create Felfel Meeting"}
                  </Button>
                  {!crmClientId && !crmDealId && (
                    <p className="mt-2 text-xs text-muted-foreground">{ar ? "اختر عميل أو صفقة أولاً لإنشاء اجتماع تلقائي." : "Select a client or deal first to auto-generate a meeting."}</p>
                  )}
                  {generatedMeeting && (
                    <div className="mt-3 space-y-2 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-3">
                      <p className="text-sm font-black text-emerald-700 dark:text-emerald-300">{generatedMeeting.title}</p>
                      <p className="truncate font-mono text-xs text-muted-foreground" dir="ltr">{generatedMeeting.meetingUrl}</p>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="rounded-xl"
                          onClick={() => { navigator.clipboard.writeText(generatedMeeting.meetingUrl); toast.success(ar ? "تم نسخ الرابط" : "Link copied"); }}
                        >
                          {ar ? "نسخ الرابط" : "Copy Link"}
                        </Button>
                        <Button asChild size="sm" variant="outline" className="rounded-xl">
                          <a href={generatedMeeting.meetingUrl} target="_blank" rel="noreferrer">
                            <ExternalLink className="me-1.5 h-3.5 w-3.5" />
                            {ar ? "فتح الاجتماع" : "Open Meeting"}
                          </a>
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
'''
    new_block = '''                {/* FELFEL_PHASE1_GENERATED_MEETING_V1 */}
                <div className="mt-1 space-y-3 border-t pt-3">
                  <div className="space-y-2">
                    <Label htmlFor="felfel-generate-client-search">{ar ? "العميل" : "Client"}</Label>
                    <Input
                      id="felfel-generate-client-search"
                      value={crmClientSearch}
                      onChange={(event) => setCrmClientSearch(event.target.value)}
                      placeholder={ar ? "ابحث بالاسم أو البريد أو الهاتف" : "Search by name, email, or phone"}
                      maxLength={120}
                    />
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={crmClientId ?? ""}
                      onChange={(event) => {
                        setCrmClientId(event.target.value ? Number(event.target.value) : null);
                        setCrmDealId(null);
                      }}
                    >
                      <option value="">{ar ? "اختر العميل" : "Select client"}</option>
                      {(crmClientsQ.data || []).map((client: any) => (
                        <option key={client.id} value={client.id}>
                          {client.name}{client.phone ? ` — ${client.phone}` : client.email ? ` — ${client.email}` : ""}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="felfel-generate-deal">{ar ? "الصفقة (اختياري)" : "Deal (optional)"}</Label>
                    <select
                      id="felfel-generate-deal"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={crmDealId ?? ""}
                      disabled={!crmClientId || crmDealsQ.isFetching}
                      onChange={(event) => setCrmDealId(event.target.value ? Number(event.target.value) : null)}
                    >
                      <option value="">{ar ? "بدون صفقة محددة" : "No specific deal"}</option>
                      {(crmDealsQ.data || []).map((deal: any) => (
                        <option key={deal.id} value={deal.id}>
                          #{deal.id} — {deal.dealType || "Deal"} — {deal.status}
                        </option>
                      ))}
                    </select>
                  </div>

                  <Button
                    onClick={() => generateMeetingM.mutate({
                      clientId: crmClientId ?? undefined,
                      leadId: undefined,
                      dealId: crmDealId ?? undefined,
                    })}
                    disabled={generateMeetingM.isPending || !crmClientId}
                    className="h-11 w-full gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-400 font-bold text-white shadow-sm hover:from-emerald-700 hover:to-emerald-500"
                  >
                    {generateMeetingM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <VideoIcon className="h-4 w-4" />}
                    {ar ? "إنشاء اجتماع بفلفل" : "Create Felfel Meeting"}
                  </Button>

                  {generatedMeeting && (
                    <div className="mt-3 space-y-2 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-3">
                      <p className="text-sm font-black text-emerald-700 dark:text-emerald-300">{generatedMeeting.title}</p>
                      <p className="truncate font-mono text-xs text-muted-foreground" dir="ltr">{generatedMeeting.meetingUrl}</p>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="rounded-xl"
                          onClick={() => { navigator.clipboard.writeText(generatedMeeting.meetingUrl); toast.success(ar ? "تم نسخ الرابط" : "Link copied"); }}
                        >
                          {ar ? "نسخ الرابط" : "Copy Link"}
                        </Button>
                        <Button asChild size="sm" variant="outline" className="rounded-xl">
                          <a href={generatedMeeting.meetingUrl} target="_blank" rel="noreferrer">
                            <ExternalLink className="me-1.5 h-3.5 w-3.5" />
                            {ar ? "فتح الاجتماع" : "Open Meeting"}
                          </a>
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
'''
    page = replace_once(page, old_block, new_block, "generated meeting UI block")
    page_path.write_text(page)

# Validate only source patch integrity here. Build/deploy stays with the applying agent.
check = subprocess.run(["git", "-C", str(ROOT), "diff", "--check"], text=True, capture_output=True)
if check.returncode != 0:
    fail("git diff --check failed: " + (check.stdout + check.stderr).strip())

changed = subprocess.check_output(["git", "-C", str(ROOT), "diff", "--name-only"], text=True).strip().splitlines()
expected = {
    "server/googleCalendar.ts",
    "server/services/felfel/felfelCrmMeetingService.ts",
    "client/src/pages/FelfelPage.tsx",
}
new_changed = [p for p in changed if p in expected]

print("PATCH=PASS")
print("BASE_HEAD=" + head)
print("ASYNC_MEET_POLLING=YES")
print("SAME_CALENDAR_EVENT_ONLY=YES")
print("ORPHAN_EVENT_CLEANUP=YES")
print("LEAD_TITLE_LOOKUP=YES")
print("PRE_MEETING_CLIENT_SELECTOR=YES")
print("PATCH_FILES=" + ",".join(sorted(new_changed)))
print("GIT_DIFF_CHECK=PASS")
print("ERROR=NONE")
