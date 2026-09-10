#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
MARKER = 'TCRM_PERMISSIONS_OPERATIONAL_MODULES_V2'


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f'MISSING_FILE={rel}')
    return path.read_text(encoding='utf-8')


def write(rel: str, content: str):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f'UPDATED={rel}')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR_ERROR={label}:expected=1:actual={count}')
    return text.replace(old, new, 1)


def replace_in_section(text: str, start: str, end: str, old: str, new: str, label: str) -> str:
    s = text.find(start)
    if s < 0:
        raise SystemExit(f'SECTION_START_MISSING={label}')
    e = text.find(end, s + len(start))
    if e < 0:
        raise SystemExit(f'SECTION_END_MISSING={label}')
    section = text[s:e]
    section2 = replace_once(section, old, new, label)
    return text[:s] + section2 + text[e:]


# 1) Central permission path policy — extend from core 3 modules to operational 4 modules.
core_policy = r'''// TCRM_PERMISSIONS_OPERATIONAL_MODULES_V2
import type { PermissionKey } from "./permissionCatalog";

type ProcedureType = "query" | "mutation" | "subscription" | string;

type CorePermissionModule =
  | "leads"
  | "deals"
  | "clients"
  | "activities"
  | "tasks"
  | "meetings"
  | "contracts";

const CORE_MODULES = new Set<CorePermissionModule>([
  "leads",
  "deals",
  "clients",
  "activities",
  "tasks",
  "meetings",
  "contracts",
]);

// Client CRUD/list routes live under accountManagement.* rather than clients.*.
const ACCOUNT_MANAGEMENT_CLIENT_OPERATIONS = new Set([
  "listclients",
  "getclientpoolstats",
  "getclientprofile",
  "getclientbusinessflow",
  "syncclientbusinessflow",
  "createclient",
  "updateclient",
  "deleteclient",
  "previewclientpoolexcel",
  "exportclientpoolexcel",
]);

// Contract CRUD/renewal routes also live under accountManagement.*.
// Sales contract handover endpoints are intentionally excluded because they are
// a separate sales->AM workflow and must keep their existing authorization.
const ACCOUNT_MANAGEMENT_CONTRACT_OPERATIONS = new Set([
  "getcontracts",
  "createcontract",
  "updatecontract",
  "getassignedrenewalcontext",
  "renewalcurrencyoptions",
  "previewrenewalcurrencyconversion",
  "addrenewalpayment",
]);

function normalizedOperation(path: string): string {
  return String(path || "")
    .split(".")
    .slice(1)
    .join("")
    .replace(/[^a-zA-Z0-9]/g, "")
    .toLowerCase();
}

function moduleFromPath(path: string): CorePermissionModule | null {
  const segments = String(path || "").split(".").filter(Boolean);
  const root = segments[0] as CorePermissionModule;
  if (CORE_MODULES.has(root)) return root;

  if (segments[0] === "accountManagement") {
    const operation = normalizedOperation(path);
    if (ACCOUNT_MANAGEMENT_CLIENT_OPERATIONS.has(operation)) return "clients";
    if (ACCOUNT_MANAGEMENT_CONTRACT_OPERATIONS.has(operation)) return "contracts";
  }

  if (segments[0] === "clientTasks") return "tasks";
  if (segments[0] === "calendar" || segments[0] === "felfel") return "meetings";
  if (segments[0] === "renewals") return "contracts";

  return null;
}

function operationFromPath(path: string): string {
  return String(path || "")
    .split(".")
    .slice(1)
    .join(".")
    .replace(/[^a-zA-Z0-9]/g, "")
    .toLowerCase();
}

function hasAny(value: string, words: readonly string[]) {
  return words.some((word) => value.includes(word));
}

/**
 * Central fail-closed permission selection at protectedProcedure boundary.
 * Row/data-scope enforcement remains a separate layer.
 */
export function resolveCorePermissionKey(path: string, type: ProcedureType): PermissionKey | null {
  const module = moduleFromPath(path);
  if (!module) return null;

  const operation = operationFromPath(path);

  if (hasAny(operation, ["export", "downloadexcel", "downloadcsv"])) {
    return `${module}.export` as PermissionKey;
  }

  if (module === "leads" && hasAny(operation, ["import", "uploadexcel", "uploadcsv"])) {
    return "leads.import";
  }

  if (type === "query" || type === "subscription") {
    return `${module}.view` as PermissionKey;
  }

  if (module === "leads" && hasAny(operation, ["reassign", "transferassignment"])) {
    return "leads.reassign";
  }

  if (module === "leads" && hasAny(operation, ["assign", "claimlead"])) {
    return "leads.assign";
  }

  if (module === "leads" && hasAny(operation, ["restore", "undelete"])) {
    return "leads.restore";
  }

  if (module === "tasks" && hasAny(operation, ["assign", "reassign"])) {
    return "tasks.assign";
  }

  if (hasAny(operation, ["delete", "remove", "purge", "trash"])) {
    return `${module}.delete` as PermissionKey;
  }

  if (hasAny(operation, ["create", "add", "new", "convert"])) {
    return `${module}.create` as PermissionKey;
  }

  return `${module}.edit` as PermissionKey;
}
'''
write('server/security/corePermissionPolicy.ts', core_policy)

core_policy_test = r'''import { describe, expect, it } from "vitest";
import { resolveCorePermissionKey } from "./corePermissionPolicy";

describe("corePermissionPolicy operational V2", () => {
  it("keeps core CRM mappings", () => {
    expect(resolveCorePermissionKey("leads.list", "query")).toBe("leads.view");
    expect(resolveCorePermissionKey("deals.updateStage", "mutation")).toBe("deals.edit");
    expect(resolveCorePermissionKey("accountManagement.listClients", "query")).toBe("clients.view");
    expect(resolveCorePermissionKey("accountManagement.createClient", "mutation")).toBe("clients.create");
  });

  it("maps activities", () => {
    expect(resolveCorePermissionKey("activities.byLead", "query")).toBe("activities.view");
    expect(resolveCorePermissionKey("activities.create", "mutation")).toBe("activities.create");
    expect(resolveCorePermissionKey("activities.update", "mutation")).toBe("activities.edit");
    expect(resolveCorePermissionKey("activities.delete", "mutation")).toBe("activities.delete");
  });

  it("maps clientTasks to tasks", () => {
    expect(resolveCorePermissionKey("clientTasks.list", "query")).toBe("tasks.view");
    expect(resolveCorePermissionKey("clientTasks.create", "mutation")).toBe("tasks.create");
    expect(resolveCorePermissionKey("clientTasks.update", "mutation")).toBe("tasks.edit");
    expect(resolveCorePermissionKey("clientTasks.delete", "mutation")).toBe("tasks.delete");
  });

  it("maps calendar and felfel to meetings", () => {
    expect(resolveCorePermissionKey("calendar.list", "query")).toBe("meetings.view");
    expect(resolveCorePermissionKey("calendar.create", "mutation")).toBe("meetings.create");
    expect(resolveCorePermissionKey("calendar.update", "mutation")).toBe("meetings.edit");
    expect(resolveCorePermissionKey("calendar.delete", "mutation")).toBe("meetings.delete");
    expect(resolveCorePermissionKey("felfel.listLinkedMeetings", "query")).toBe("meetings.view");
    expect(resolveCorePermissionKey("felfel.createLinkedMeeting", "mutation")).toBe("meetings.create");
  });

  it("maps actual accountManagement contract endpoints", () => {
    expect(resolveCorePermissionKey("accountManagement.getContracts", "query")).toBe("contracts.view");
    expect(resolveCorePermissionKey("accountManagement.createContract", "mutation")).toBe("contracts.create");
    expect(resolveCorePermissionKey("accountManagement.updateContract", "mutation")).toBe("contracts.edit");
    expect(resolveCorePermissionKey("accountManagement.addRenewalPayment", "mutation")).toBe("contracts.create");
    expect(resolveCorePermissionKey("renewals.list", "query")).toBe("contracts.view");
    expect(resolveCorePermissionKey("renewals.updateStage", "mutation")).toBe("contracts.edit");
  });

  it("does not hijack sales contract handover", () => {
    expect(resolveCorePermissionKey("accountManagement.submitSalesContractHandover", "mutation")).toBeNull();
    expect(resolveCorePermissionKey("accountManagement.getSalesContractHandoverStatus", "query")).toBeNull();
  });
});
'''
write('server/security/corePermissionPolicy.test.ts', core_policy_test)

# 2) Operational row-scope layer.
operational_scope = r'''// TCRM_PERMISSIONS_OPERATIONAL_MODULES_V2
import { TRPCError } from "@trpc/server";
import {
  getActivityById,
  getClientById,
  getClientTaskMeta,
  getContractById,
  getLeadById,
  getUserById,
} from "../db";
import type { PermissionDecision, PermissionUser } from "./permissionEngine";
import { evaluatePermission } from "./permissionEngine";
import { isRowInScope } from "./phase3ScopeFilters";

export type OperationalPermissionModule = "activities" | "tasks" | "meetings" | "contracts";

type OperationalContext = {
  user: PermissionUser;
  permissionDecision?: PermissionDecision | null;
  req?: object | null;
};

export function getOperationalPermissionDecision(ctx: OperationalContext | any, module: OperationalPermissionModule) {
  const decision = ctx?.permissionDecision as PermissionDecision | undefined;
  if (!decision?.allowed) return null;
  if (!String(decision.permission || "").startsWith(`${module}.`)) return null;
  return decision;
}

function requireDecision(ctx: OperationalContext | any, module: OperationalPermissionModule): PermissionDecision {
  const decision = getOperationalPermissionDecision(ctx, module);
  if (!decision) {
    throw new TRPCError({ code: "FORBIDDEN", message: `Missing effective ${module} permission decision` });
  }
  return decision;
}

function scopedUser(ctx: OperationalContext | any): PermissionUser {
  return {
    id: Number(ctx?.user?.id ?? 0),
    role: String(ctx?.user?.role ?? ""),
    email: ctx?.user?.email ?? null,
    teamId: ctx?.user?.teamId ?? null,
  };
}

function deny(module: OperationalPermissionModule) {
  throw new TRPCError({ code: "FORBIDDEN", message: `${module} record is outside your permission scope` });
}

async function assertLeadLinked(ctx: any, module: OperationalPermissionModule, leadId: number) {
  const decision = requireDecision(ctx, module);
  const lead = await getLeadById(Number(leadId));
  if (!lead || (lead as any).deletedAt) throw new TRPCError({ code: "NOT_FOUND", message: "Lead not found" });
  if (!(await isRowInScope("lead", decision, scopedUser(ctx), lead))) deny(module);
  return lead;
}

async function assertClientLinked(ctx: any, module: OperationalPermissionModule, clientId: number) {
  const decision = requireDecision(ctx, module);
  const client = await getClientById(Number(clientId));
  if (!client || (client as any).deletedAt) throw new TRPCError({ code: "NOT_FOUND", message: "Client not found" });
  if (!(await isRowInScope("client", decision, scopedUser(ctx), client))) deny(module);
  return client;
}

export async function assertActivityLeadScopeForContext(ctx: any, leadId: number) {
  return assertLeadLinked(ctx, "activities", leadId);
}

export async function assertActivityUserScopeForContext(ctx: any, targetUserId: number) {
  const decision = requireDecision(ctx, "activities");
  const user = scopedUser(ctx);
  const uid = Number(user.id);
  const targetId = Number(targetUserId);
  if (decision.scope === "all") return true;
  if ((decision.scope === "own" || decision.scope === "assigned") && targetId === uid) return true;
  if (decision.scope === "team") {
    const teamId = Number(user.teamId ?? 0);
    const target = await getUserById(targetId);
    if (teamId > 0 && target && !(target as any).deletedAt && Number((target as any).teamId ?? 0) === teamId) return true;
  }
  deny("activities");
}

export async function assertActivityScopeForContext(ctx: any, activityId: number) {
  const decision = requireDecision(ctx, "activities");
  const activity: any = await getActivityById(Number(activityId));
  if (!activity || activity.deletedAt) throw new TRPCError({ code: "NOT_FOUND", message: "Activity not found" });
  if (Number(activity.leadId ?? 0) > 0) {
    await assertLeadLinked(ctx, "activities", Number(activity.leadId));
    return activity;
  }
  const user = scopedUser(ctx);
  const actorId = Number(activity.userId ?? activity.createdBy ?? 0);
  if (decision.scope === "all") return activity;
  if ((decision.scope === "own" || decision.scope === "assigned") && actorId === Number(user.id)) return activity;
  if (decision.scope === "team") {
    const target = await getUserById(actorId);
    if (target && Number(user.teamId ?? 0) > 0 && Number((target as any).teamId ?? 0) === Number(user.teamId)) return activity;
  }
  deny("activities");
}

export async function assertTaskClientScopeForContext(ctx: any, clientId: number) {
  return assertClientLinked(ctx, "tasks", clientId);
}

export async function assertTaskScopeForContext(ctx: any, taskId: number) {
  const decision = requireDecision(ctx, "tasks");
  const meta: any = await getClientTaskMeta(Number(taskId)).catch(() => null);
  if (!meta || meta.deletedAt) throw new TRPCError({ code: "NOT_FOUND", message: "Task not found" });
  const uid = Number(ctx.user.id);
  if (decision.scope === "all") return meta;
  if (decision.scope === "own" && (Number(meta.createdBy ?? 0) === uid || Number(meta.assignedTo ?? 0) === uid)) return meta;
  if (decision.scope === "assigned" && Number(meta.assignedTo ?? 0) === uid) return meta;
  if (Number(meta.clientId ?? 0) > 0) {
    await assertClientLinked(ctx, "tasks", Number(meta.clientId));
    return meta;
  }
  deny("tasks");
}

export async function assertTaskAssignmentPermission(ctx: any) {
  const decision = await evaluatePermission(ctx.user, "tasks.assign", undefined);
  if (!decision.allowed) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Permission denied: tasks.assign" });
  }
  return decision;
}

export async function assertContractClientScopeForContext(ctx: any, clientId: number) {
  return assertClientLinked(ctx, "contracts", clientId);
}

export async function assertContractScopeForContext(ctx: any, contractId: number) {
  const contract: any = await getContractById(Number(contractId)).catch(() => null);
  if (!contract || contract.deletedAt) throw new TRPCError({ code: "NOT_FOUND", message: "Contract not found" });
  await assertClientLinked(ctx, "contracts", Number(contract.clientId));
  return contract;
}

export async function assertMeetingCreateScopeForContext(ctx: any, resource?: { leadId?: number | null; clientId?: number | null }) {
  const decision = requireDecision(ctx, "meetings");
  if (resource?.leadId) return assertLeadLinked(ctx, "meetings", Number(resource.leadId));
  if (resource?.clientId) return assertClientLinked(ctx, "meetings", Number(resource.clientId));
  if (["all", "own", "assigned", "team"].includes(decision.scope)) return true;
  deny("meetings");
}

export type CalendarScopedEvent = {
  ownerUserId?: number | null;
  leadId?: number | null;
};

export async function assertCalendarEventScopeForContext(ctx: any, event: CalendarScopedEvent) {
  const decision = requireDecision(ctx, "meetings");
  const user = scopedUser(ctx);
  if (decision.scope === "all") return true;
  if (Number(event?.leadId ?? 0) > 0) {
    await assertLeadLinked(ctx, "meetings", Number(event.leadId));
    return true;
  }
  const ownerId = Number(event?.ownerUserId ?? 0);
  if ((decision.scope === "own" || decision.scope === "assigned") && ownerId === Number(user.id)) return true;
  if (decision.scope === "team" && ownerId > 0) {
    const owner = await getUserById(ownerId);
    if (owner && Number(user.teamId ?? 0) > 0 && Number((owner as any).teamId ?? 0) === Number(user.teamId)) return true;
  }
  deny("meetings");
}

export async function filterCalendarEventsForContext<T extends CalendarScopedEvent>(ctx: any, events: T[]): Promise<T[]> {
  if (requireDecision(ctx, "meetings").scope === "all") return events;
  const checks = await Promise.all(events.map(async (event) => {
    try {
      await assertCalendarEventScopeForContext(ctx, event);
      return true;
    } catch {
      return false;
    }
  }));
  return events.filter((_, index) => checks[index]);
}

export async function assertFelfelMeetingScopeForContext(ctx: any, meeting: any) {
  const decision = requireDecision(ctx, "meetings");
  if (decision.scope === "all") return meeting;
  if (Number(meeting?.leadId ?? 0) > 0) {
    await assertLeadLinked(ctx, "meetings", Number(meeting.leadId));
    return meeting;
  }
  if (Number(meeting?.clientId ?? 0) > 0) {
    await assertClientLinked(ctx, "meetings", Number(meeting.clientId));
    return meeting;
  }
  await assertCalendarEventScopeForContext(ctx, { ownerUserId: Number(meeting?.ownerUserId ?? meeting?.createdByUserId ?? 0) });
  return meeting;
}
'''
write('server/security/operationalScopeEnforcement.ts', operational_scope)

operational_scope_test = r'''import { describe, expect, it } from "vitest";
import { getOperationalPermissionDecision } from "./operationalScopeEnforcement";

function ctx(permission: string, scope = "assigned") {
  return {
    user: { id: 7, role: "AccountManager", teamId: 3 },
    permissionDecision: { allowed: true, permission, scope, source: "role" },
  } as any;
}

describe("operationalScopeEnforcement", () => {
  it("accepts matching operational decisions", () => {
    expect(getOperationalPermissionDecision(ctx("activities.view"), "activities")?.scope).toBe("assigned");
    expect(getOperationalPermissionDecision(ctx("tasks.edit", "team"), "tasks")?.scope).toBe("team");
    expect(getOperationalPermissionDecision(ctx("meetings.view", "own"), "meetings")?.scope).toBe("own");
    expect(getOperationalPermissionDecision(ctx("contracts.view", "all"), "contracts")?.scope).toBe("all");
  });

  it("rejects a decision from another module", () => {
    expect(getOperationalPermissionDecision(ctx("deals.view"), "activities")).toBeNull();
    expect(getOperationalPermissionDecision(ctx("clients.view"), "contracts")).toBeNull();
  });
});
'''
write('server/security/operationalScopeEnforcement.test.ts', operational_scope_test)

# 3) Persist owner/link metadata in Google Calendar private extended properties.
google_calendar = r'''/**
 * Google Calendar Integration Service
 * Uses a Service Account to manage calendar events for Tamiyouz CRM.
 */
// TCRM_PERMISSIONS_OPERATIONAL_MODULES_V2
import { google } from "googleapis";
import path from "path";
import fs from "fs";

const CALENDAR_ID = "veo3.tamiyouz@gmail.com";
const KEY_FILE_PATH = path.join(import.meta.dirname, "google-calendar-key.json");

let _calendarClient: ReturnType<typeof google.calendar> | null = null;

async function getCalendarClient() {
  if (_calendarClient) return _calendarClient;
  if (!fs.existsSync(KEY_FILE_PATH)) throw new Error(`Google Calendar key file not found at ${KEY_FILE_PATH}`);
  const auth = new google.auth.GoogleAuth({
    keyFile: KEY_FILE_PATH,
    scopes: ["https://www.googleapis.com/auth/calendar"],
  });
  _calendarClient = google.calendar({ version: "v3", auth });
  return _calendarClient;
}

export interface CalendarEvent {
  id?: string;
  summary: string;
  description?: string;
  location?: string;
  startDateTime: string;
  endDateTime: string;
  attendees?: string[];
  leadId?: number;
  leadName?: string;
  agentName?: string;
  ownerUserId?: number;
}

export interface CalendarEventResult {
  id: string;
  htmlLink: string;
  summary: string;
  description?: string;
  location?: string;
  start: string;
  end: string;
  status: string;
  attendees?: { email: string; responseStatus?: string }[];
  leadId?: number;
  ownerUserId?: number;
}

function positiveInt(value: unknown): number | undefined {
  const n = Number(value ?? 0);
  return Number.isInteger(n) && n > 0 ? n : undefined;
}

function toResult(data: any): CalendarEventResult {
  const privateProps = data?.extendedProperties?.private || {};
  return {
    id: data.id!,
    htmlLink: data.htmlLink!,
    summary: data.summary || "",
    description: data.description || undefined,
    location: data.location || undefined,
    start: data.start?.dateTime || data.start?.date || "",
    end: data.end?.dateTime || data.end?.date || "",
    status: data.status || "confirmed",
    attendees: data.attendees?.map((a: any) => ({ email: a.email!, responseStatus: a.responseStatus || undefined })),
    leadId: positiveInt(privateProps.tcrmLeadId),
    ownerUserId: positiveInt(privateProps.tcrmOwnerUserId),
  };
}

function privateMetadata(event: Partial<CalendarEvent>) {
  const data: Record<string, string> = {};
  if (positiveInt(event.ownerUserId)) data.tcrmOwnerUserId = String(event.ownerUserId);
  if (positiveInt(event.leadId)) data.tcrmLeadId = String(event.leadId);
  return data;
}

export async function createCalendarEvent(event: CalendarEvent): Promise<CalendarEventResult> {
  const calendar = await getCalendarClient();
  const description = [
    event.description || "",
    "",
    "─── CRM Details ───",
    event.leadId ? `Lead ID: ${event.leadId}` : "",
    event.leadName ? `Lead Name: ${event.leadName}` : "",
    event.agentName ? `Agent: ${event.agentName}` : "",
    "Created from Tamiyouz CRM",
  ].filter(Boolean).join("\n");

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
    eventBody.description = (eventBody.description || "") + "\n\nAttendees: " + event.attendees.join(", ");
  }

  const response = await calendar.events.insert({ calendarId: CALENDAR_ID, requestBody: eventBody });
  return toResult(response.data);
}

export async function updateCalendarEvent(eventId: string, event: Partial<CalendarEvent>): Promise<CalendarEventResult> {
  const calendar = await getCalendarClient();
  const updateBody: any = {};
  if (event.summary) updateBody.summary = event.summary;
  if (event.description !== undefined) updateBody.description = event.description;
  if (event.location !== undefined) updateBody.location = event.location;
  if (event.startDateTime) updateBody.start = { dateTime: event.startDateTime, timeZone: "Asia/Riyadh" };
  if (event.endDateTime) updateBody.end = { dateTime: event.endDateTime, timeZone: "Asia/Riyadh" };
  const metadata = privateMetadata(event);
  if (Object.keys(metadata).length) updateBody.extendedProperties = { private: metadata };
  const response = await calendar.events.patch({ calendarId: CALENDAR_ID, eventId, requestBody: updateBody });
  return toResult(response.data);
}

export async function deleteCalendarEvent(eventId: string): Promise<void> {
  const calendar = await getCalendarClient();
  await calendar.events.delete({ calendarId: CALENDAR_ID, eventId, sendUpdates: "all" });
}

export async function getCalendarEvent(eventId: string): Promise<CalendarEventResult | null> {
  const calendar = await getCalendarClient();
  try {
    const response = await calendar.events.get({ calendarId: CALENDAR_ID, eventId });
    return toResult(response.data);
  } catch (err: any) {
    if (err.code === 404) return null;
    throw err;
  }
}

export async function listCalendarEvents(options?: {
  timeMin?: string;
  timeMax?: string;
  maxResults?: number;
  search?: string;
}): Promise<CalendarEventResult[]> {
  const calendar = await getCalendarClient();
  const params: any = {
    calendarId: CALENDAR_ID,
    singleEvents: true,
    orderBy: "startTime",
    maxResults: options?.maxResults || 50,
  };
  if (options?.timeMin) params.timeMin = options.timeMin;
  if (options?.timeMax) params.timeMax = options.timeMax;
  if (options?.search) params.q = options.search;
  const response = await calendar.events.list(params);
  return (response.data.items || []).map(toResult);
}

export async function getFreeBusy(timeMin: string, timeMax: string): Promise<{ start: string; end: string }[]> {
  const calendar = await getCalendarClient();
  const response = await calendar.freebusy.query({
    requestBody: {
      timeMin,
      timeMax,
      timeZone: "Asia/Riyadh",
      items: [{ id: CALENDAR_ID }],
    },
  });
  const busy = response.data.calendars?.[CALENDAR_ID]?.busy || [];
  return busy.map((b) => ({ start: b.start || "", end: b.end || "" }));
}
'''
write('server/googleCalendar.ts', google_calendar)

# 4) Routers: import operational scope helpers.
routers = read('server/routers.ts')
if MARKER not in routers:
    import_anchor = '''import {\n  assertClientScopeForContext,\n  assertCreateOwnerScopeForContext,\n  assertDealLeadScopeForContext,\n  assertLeadScopeForContext,\n  filterDealRowsForContext,\n  getCoreListScopeFilter,\n  getCorePermissionDecision,\n} from "./security/coreScopeEnforcement";'''
    import_new = import_anchor + '''\nimport {\n  assertActivityLeadScopeForContext,\n  assertActivityScopeForContext,\n  assertActivityUserScopeForContext,\n  assertCalendarEventScopeForContext,\n  assertContractClientScopeForContext,\n  assertContractScopeForContext,\n  assertFelfelMeetingScopeForContext,\n  assertMeetingCreateScopeForContext,\n  assertTaskAssignmentPermission,\n  assertTaskClientScopeForContext,\n  assertTaskScopeForContext,\n  filterCalendarEventsForContext,\n} from "./security/operationalScopeEnforcement";\n// TCRM_PERMISSIONS_OPERATIONAL_MODULES_V2'''
    routers = replace_once(routers, import_anchor, import_new, 'routers_import')

    # Activities — use activities permission scope, not deals scope, and protect update/delete by persisted record.
    activities_start = '  // ─── Activities (with row-level security)'
    activities_end = '  // ─── Deals (with row-level security)'
    routers = replace_in_section(
        routers, activities_start, activities_end,
        '''        if (getCorePermissionDecision(ctx, "deals")) {\n          await assertDealLeadScopeForContext(ctx, input.leadId);\n        }''',
        '''        await assertActivityLeadScopeForContext(ctx, input.leadId);''',
        'activities_byLead_scope',
    )
    routers = replace_in_section(
        routers, activities_start, activities_end,
        '''        if (getCorePermissionDecision(ctx, "deals")) {\n          await assertDealLeadScopeForContext(ctx, input.leadId);\n        }''',
        '''        await assertActivityLeadScopeForContext(ctx, input.leadId);''',
        'activities_create_scope',
    )
    routers = replace_in_section(
        routers, activities_start, activities_end,
        '''      .query(({ ctx, input }) => {\n        const userId = input.userId ?? ctx.user.id;''',
        '''      .query(async ({ ctx, input }) => {\n        const userId = input.userId ?? ctx.user.id;\n        await assertActivityUserScopeForContext(ctx, userId);''',
        'activities_byUser_scope',
    )
    routers = replace_in_section(
        routers, activities_start, activities_end,
        '''      .mutation(({ input }) => {\n        const { id, ...data } = input;\n        return updateActivity(id, data as any);\n      }),''',
        '''      .mutation(async ({ ctx, input }) => {\n        const { id, ...data } = input;\n        await assertActivityScopeForContext(ctx, id);\n        return updateActivity(id, data as any);\n      }),''',
        'activities_update_scope',
    )
    routers = replace_in_section(
        routers, activities_start, activities_end,
        '''      .mutation(async ({ ctx, input }) => {\n        if (getCorePermissionDecision(ctx, "deals") && input.leadId) {\n          await assertDealLeadScopeForContext(ctx, input.leadId);\n        }\n        const existing = await getActivityById(input.id);''',
        '''      .mutation(async ({ ctx, input }) => {\n        const existing = await assertActivityScopeForContext(ctx, input.id);''',
        'activities_delete_scope',
    )
    routers = replace_in_section(
        routers, activities_start, activities_end,
        '''                  leadName,\n                  agentName: agentDisplayName,\n                });''',
        '''                  leadName,\n                  agentName: agentDisplayName,\n                  ownerUserId: ctx.user.id,\n                });''',
        'activities_calendar_owner',
    )

    # Calendar / meetings — persist creator identity and enforce scope on list/read/write.
    calendar_start = '  // ─── Google Calendar'
    calendar_end = '  // ─── In-App Notifications'
    routers = replace_in_section(
        routers, calendar_start, calendar_end,
        '''      .query(async ({ input }) => {\n        return listCalendarEvents({\n          timeMin: input?.timeMin,\n          timeMax: input?.timeMax,\n          maxResults: input?.maxResults,\n          search: input?.search,\n        });\n      }),''',
        '''      .query(async ({ ctx, input }) => {\n        const events = await listCalendarEvents({\n          timeMin: input?.timeMin,\n          timeMax: input?.timeMax,\n          maxResults: input?.maxResults,\n          search: input?.search,\n        });\n        return filterCalendarEventsForContext(ctx, events);\n      }),''',
        'calendar_list_scope',
    )
    routers = replace_in_section(
        routers, calendar_start, calendar_end,
        '''      .query(async ({ input }) => {\n        return getCalendarEvent(input.eventId);\n      }),''',
        '''      .query(async ({ ctx, input }) => {\n        const event = await getCalendarEvent(input.eventId);\n        if (!event) return null;\n        await assertCalendarEventScopeForContext(ctx, event);\n        return event;\n      }),''',
        'calendar_get_scope',
    )
    routers = replace_in_section(
        routers, calendar_start, calendar_end,
        '''      .mutation(async ({ ctx, input }) => {\n        // Include creator's email in attendees list''',
        '''      .mutation(async ({ ctx, input }) => {\n        await assertMeetingCreateScopeForContext(ctx, { leadId: input.leadId });\n        // Include creator's email in attendees list''',
        'calendar_create_scope',
    )
    routers = replace_in_section(
        routers, calendar_start, calendar_end,
        '''          attendees,\n          agentName,\n        });''',
        '''          attendees,\n          agentName,\n          ownerUserId: ctx.user.id,\n        });''',
        'calendar_create_owner',
    )
    routers = replace_in_section(
        routers, calendar_start, calendar_end,
        '''      .mutation(async ({ ctx, input }) => {\n        const { eventId, ...updateData } = input;\n        const result = await updateCalendarEvent(eventId, updateData);''',
        '''      .mutation(async ({ ctx, input }) => {\n        const { eventId, ...updateData } = input;\n        const existingEvent = await getCalendarEvent(eventId);\n        if (!existingEvent) throw new TRPCError({ code: "NOT_FOUND", message: "Calendar event not found" });\n        await assertCalendarEventScopeForContext(ctx, existingEvent);\n        const result = await updateCalendarEvent(eventId, updateData);''',
        'calendar_update_scope',
    )
    routers = replace_in_section(
        routers, calendar_start, calendar_end,
        '''      .mutation(async ({ ctx, input }) => {\n        await deleteCalendarEvent(input.eventId);''',
        '''      .mutation(async ({ ctx, input }) => {\n        const existingEvent = await getCalendarEvent(input.eventId);\n        if (!existingEvent) throw new TRPCError({ code: "NOT_FOUND", message: "Calendar event not found" });\n        await assertCalendarEventScopeForContext(ctx, existingEvent);\n        await deleteCalendarEvent(input.eventId);''',
        'calendar_delete_scope',
    )

    # Contracts — permission scope is based on the linked client assignment/team.
    account_start = '  // ─── Account Management'
    account_end = '  // ─── Phase 3: Onboarding'
    routers = replace_in_section(
        routers, account_start, account_end,
        '''    getContracts: clientOpsProcedure\n      .input(z.object({ clientId: z.number() }))\n      .query(async ({ input, ctx }) => {\n        await assertAccountManagementClientAccess(ctx, input.clientId);''',
        '''    getContracts: protectedProcedure\n      .input(z.object({ clientId: z.number() }))\n      .query(async ({ input, ctx }) => {\n        await assertContractClientScopeForContext(ctx, input.clientId);''',
        'contracts_list_scope',
    )
    routers = replace_in_section(
        routers, account_start, account_end,
        '''    createContract: clientWriteProcedure''',
        '''    createContract: protectedProcedure''',
        'contracts_create_procedure',
    )
    routers = replace_in_section(
        routers, account_start, account_end,
        '''      .mutation(async ({ input, ctx }) => {\n        await assertAccountManagementClientAccess(ctx, input.clientId, "contract.create");''',
        '''      .mutation(async ({ input, ctx }) => {\n        await assertContractClientScopeForContext(ctx, input.clientId);''',
        'contracts_create_scope',
    )
    routers = replace_in_section(
        routers, account_start, account_end,
        '''    updateContract: clientWriteProcedure''',
        '''    updateContract: protectedProcedure''',
        'contracts_update_procedure',
    )
    routers = replace_in_section(
        routers, account_start, account_end,
        '''        const { id, ...data } = input;\n        const existing = await assertAccountManagementContractAccess(ctx, id, "contract.update");''',
        '''        const { id, ...data } = input;\n        const existing = await assertContractScopeForContext(ctx, id);''',
        'contracts_update_scope',
    )

    # Client Tasks — add scope without replacing existing task/TOS business rules.
    tasks_start = '  // ─── Phase 3: Client Tasks'
    tasks_end = '  // ─── Phase 3: Onboarding'
    routers = replace_in_section(
        routers, tasks_start, tasks_end,
        '''      .query(async ({ input, ctx }) => {\n        const role = normalizeUserRole(ctx.user.role);''',
        '''      .query(async ({ input, ctx }) => {\n        const role = normalizeUserRole(ctx.user.role);\n        await assertTaskClientScopeForContext(ctx, input.clientId);''',
        'tasks_list_scope',
    )
    routers = replace_in_section(
        routers, tasks_start, tasks_end,
        '''      .mutation(async ({ input, ctx }) => {\n        await assertAccountManagementClientAccess(ctx, input.clientId, "client.update");''',
        '''      .mutation(async ({ input, ctx }) => {\n        await assertTaskClientScopeForContext(ctx, input.clientId);\n        await assertTaskAssignmentPermission(ctx);''',
        'tasks_create_scope_assign',
    )
    routers = replace_in_section(
        routers, tasks_start, tasks_end,
        '''      .mutation(async ({ input, ctx }) => {\n        const meta: any = await getClientTaskMeta(input.id);\n        const role = normalizeUserRole(ctx.user.role);''',
        '''      .mutation(async ({ input, ctx }) => {\n        const meta: any = await getClientTaskMeta(input.id);\n        await assertTaskScopeForContext(ctx, input.id);\n        const role = normalizeUserRole(ctx.user.role);\n        if (input.data.assignedTo !== undefined || input.data.tosAssigneeUserId !== undefined || input.data.tosFollowerUserIds !== undefined) {\n          await assertTaskAssignmentPermission(ctx);\n        }''',
        'tasks_update_scope_assign',
    )
    routers = replace_in_section(
        routers, tasks_start, tasks_end,
        '''      .mutation(async ({ input, ctx }) => {\n        const meta = await getClientTaskMeta(input.id);\n        await assertTaskOperationAllowed''',
        '''      .mutation(async ({ input, ctx }) => {\n        const meta = await getClientTaskMeta(input.id);\n        await assertTaskScopeForContext(ctx, input.id);\n        await assertTaskOperationAllowed''',
        'tasks_delete_scope',
    )

    # Felfel linked meetings keep their existing authorization and additionally honor meetings.* scope.
    felfel_start = '  felfel: router({'
    felfel_end = '  auth:'
    routers = replace_in_section(
        routers, felfel_start, felfel_end,
        '''        const context = await assertFelfelCreateContext(ctx.user as any, input);\n        return createLinkedFelfelMeeting''',
        '''        const context = await assertFelfelCreateContext(ctx.user as any, input);\n        await assertMeetingCreateScopeForContext(ctx, { leadId: context.leadId || input.leadId, clientId: context.clientId || input.clientId });\n        return createLinkedFelfelMeeting''',
        'felfel_create_scope',
    )
    routers = replace_in_section(
        routers, felfel_start, felfel_end,
        '''        const meeting = await getLinkedFelfelMeeting(input.id);\n        await assertFelfelMeetingAccess(ctx.user as any, { meetingId: input.id });\n        return meeting;''',
        '''        const meeting = await getLinkedFelfelMeeting(input.id);\n        await assertFelfelMeetingAccess(ctx.user as any, { meetingId: input.id });\n        await assertFelfelMeetingScopeForContext(ctx, meeting);\n        return meeting;''',
        'felfel_get_scope',
    )

write('server/routers.ts', routers)

# 5) Preserve legacy after-sales task behavior only when no explicit permission grant/deny exists.
trpc = read('server/_core/trpc.ts')
if 'TCRM_OPERATIONAL_TASK_LEGACY_FALLBACK_V2' not in trpc:
    old = '''  if (!decision.allowed) {\n    throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${permission}` });\n  }\n\n  return opts.next({\n    ctx: { ...opts.ctx, permissionDecision: decision } as any,\n  });'''
    new = '''  if (!decision.allowed) {\n    // TCRM_OPERATIONAL_TASK_LEGACY_FALLBACK_V2\n    // Existing after-sales roles historically have assigned client-task access.\n    // Preserve that only when the new engine has no explicit role/user decision.\n    const legacyTaskRole = ["ServiceAdvisor", "PartsAgent", "CrmFollowUp"].includes(String(opts.ctx.user?.role || ""));\n    const legacyTaskPermission = permission === "tasks.view" || permission === "tasks.edit";\n    if (decision.source === "none" && legacyTaskRole && legacyTaskPermission) {\n      return opts.next({\n        ctx: {\n          ...opts.ctx,\n          permissionDecision: { allowed: true, permission, scope: "assigned", source: "legacy_role" },\n        } as any,\n      });\n    }\n    throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${permission}` });\n  }\n\n  return opts.next({\n    ctx: { ...opts.ctx, permissionDecision: decision } as any,\n  });'''
    trpc = replace_once(trpc, old, new, 'trpc_legacy_task_fallback')
    write('server/_core/trpc.ts', trpc)
else:
    print('SKIP=server/_core/trpc.ts:already_patched')

print('PATCH=TCRM-PERMISSIONS-OPERATIONAL-MODULES-V2')
print('BASELINE=61c66cf4ec8fe2695cf798dc10ab48084066a90d')
print('MODULES=activities,tasks,meetings,contracts')
print('SERVER_PERMISSION_GATE=EXTENDED')
print('ROW_SCOPE=own,assigned,team,all')
print('GOOGLE_CALENDAR_PRIVATE_OWNER_METADATA=YES')
print('FELFEL_EXISTING_AUTH_PRESERVED=YES')
print('TASK_EXISTING_TOS_BUSINESS_RULES_PRESERVED=YES')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
