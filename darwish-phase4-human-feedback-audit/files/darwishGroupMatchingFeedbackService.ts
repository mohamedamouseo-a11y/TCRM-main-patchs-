import { sql } from "drizzle-orm";
import { getDb } from "../../../db";
import {
  rankDarwishGroupCandidatesForClient,
  type DarwishGroupMatchingCandidate,
  type DarwishSmartGroupCandidate,
} from "./darwishSmartGroupMatchingService";

export const DARWISH_GROUP_MATCHING_FEEDBACK_DECISIONS = [
  "accepted_recommendation",
  "overrode_recommendation",
  "manual_without_recommendation",
] as const;

export type DarwishGroupMatchingFeedbackDecision =
  typeof DARWISH_GROUP_MATCHING_FEEDBACK_DECISIONS[number];

type GroupJob = {
  groupJid?: unknown;
  groupName?: unknown;
  evolutionInstance?: unknown;
  chatwootConversationId?: unknown;
  receivedAt?: unknown;
  messageTimestamp?: unknown;
};

type GroupLink = {
  clientId?: unknown;
  groupJid?: unknown;
  evolutionInstance?: unknown;
  enabled?: unknown;
};

export type DarwishGroupMatchingFeedbackSnapshot = {
  clientId: number;
  actorUserId: number;
  decisionType: DarwishGroupMatchingFeedbackDecision;
  selectedGroupJid: string;
  selectedEvolutionInstance: string;
  recommendationAvailable: boolean;
  recommendedGroupJid: string | null;
  recommendedEvolutionInstance: string | null;
  selectedIsRecommended: boolean;
  selectedConfidence: number | null;
  selectedConfidenceLevel: DarwishSmartGroupCandidate["smartConfidenceLevel"];
  selectedSignals: string[];
  recommendedConfidence: number | null;
  recommendedConfidenceLevel: DarwishSmartGroupCandidate["smartConfidenceLevel"];
};

const SAFE_SIGNAL_VALUES = new Set([
  "exact_phone",
  "name",
  "business_name",
  "group_name",
  "participant_name",
  "sender_identity",
  "message_context",
  "other",
]);

function identity(groupJid: unknown, evolutionInstance: unknown) {
  return `${String(evolutionInstance || "").trim()}::${String(groupJid || "").trim()}`;
}

function positiveInt(value: unknown, label: string) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) throw new Error(`${label} must be a positive integer`);
  return parsed;
}

function identityText(value: unknown, label: string, max: number) {
  const text = String(value || "").trim();
  if (!text || text.length > max) throw new Error(`${label} is invalid`);
  return text;
}

function confidence(value: unknown) {
  if (value == null) return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return null;
  return Math.max(0, Math.min(100, parsed));
}

function signals(values: unknown) {
  if (!Array.isArray(values)) return [];
  return [...new Set(
    values
      .map((value) => String(value || "").trim())
      .filter((value) => SAFE_SIGNAL_VALUES.has(value)),
  )].slice(0, 8);
}

export function __buildDarwishGroupCandidatesForFeedbackTests(input: {
  clientId: number;
  jobs: GroupJob[];
  linksBefore: GroupLink[];
}): DarwishGroupMatchingCandidate[] {
  const clientId = positiveInt(input.clientId, "clientId");
  const linkByIdentity = new Map<string, GroupLink>();

  for (const link of input.linksBefore || []) {
    if (Number(link?.enabled ?? 1) !== 1) continue;
    const groupJid = String(link?.groupJid || "").trim();
    const evolutionInstance = String(link?.evolutionInstance || "").trim();
    if (groupJid && evolutionInstance) linkByIdentity.set(identity(groupJid, evolutionInstance), link);
  }

  const seen = new Set<string>();
  const result: DarwishGroupMatchingCandidate[] = [];
  for (const job of input.jobs || []) {
    const groupJid = String(job?.groupJid || "").trim();
    const evolutionInstance = String(job?.evolutionInstance || "").trim();
    if (!groupJid || !evolutionInstance) continue;
    const key = identity(groupJid, evolutionInstance);
    if (seen.has(key)) continue;
    seen.add(key);

    const link = linkByIdentity.get(key);
    const linkedRaw = Number(link?.clientId);
    const linkedClientId = Number.isInteger(linkedRaw) && linkedRaw > 0 ? linkedRaw : null;
    const status: DarwishGroupMatchingCandidate["status"] = linkedClientId === clientId
      ? "linked_current"
      : linkedClientId
        ? "linked_other"
        : "unlinked";

    result.push({
      groupJid,
      groupName: String(job?.groupName || "").trim() || null,
      evolutionInstance,
      chatwootConversationId: String(job?.chatwootConversationId || "").trim() || null,
      lastActivityAt: job?.receivedAt ?? job?.messageTimestamp ?? null,
      linkedClientId,
      status,
      eligible: linkedClientId === null || linkedClientId === clientId,
    });
  }
  return result;
}

export function __buildDarwishGroupMatchingFeedbackSnapshotForTests(input: {
  clientId: number;
  actorUserId: number;
  selectedGroupJid: string;
  selectedEvolutionInstance: string;
  rankedCandidates: DarwishSmartGroupCandidate[];
}): DarwishGroupMatchingFeedbackSnapshot {
  const clientId = positiveInt(input.clientId, "clientId");
  const actorUserId = positiveInt(input.actorUserId, "actorUserId");
  const selectedGroupJid = identityText(input.selectedGroupJid, "selectedGroupJid", 255);
  const selectedEvolutionInstance = identityText(input.selectedEvolutionInstance, "selectedEvolutionInstance", 160);
  const selectedKey = identity(selectedGroupJid, selectedEvolutionInstance);
  const selected = input.rankedCandidates.find(
    (candidate) => identity(candidate.groupJid, candidate.evolutionInstance) === selectedKey,
  );
  if (!selected) throw new Error("Selected WhatsApp group is missing from the server ranking snapshot");

  const recommended = input.rankedCandidates.find((candidate) => candidate.darwishRecommended) ?? null;
  const selectedIsRecommended = Boolean(
    recommended && identity(recommended.groupJid, recommended.evolutionInstance) === selectedKey,
  );
  const decisionType: DarwishGroupMatchingFeedbackDecision = recommended
    ? selectedIsRecommended
      ? "accepted_recommendation"
      : "overrode_recommendation"
    : "manual_without_recommendation";

  return {
    clientId,
    actorUserId,
    decisionType,
    selectedGroupJid,
    selectedEvolutionInstance,
    recommendationAvailable: Boolean(recommended),
    recommendedGroupJid: recommended?.groupJid ?? null,
    recommendedEvolutionInstance: recommended?.evolutionInstance ?? null,
    selectedIsRecommended,
    selectedConfidence: confidence(selected.smartConfidence),
    selectedConfidenceLevel: selected.smartConfidenceLevel,
    selectedSignals: signals(selected.smartSignals),
    recommendedConfidence: confidence(recommended?.smartConfidence),
    recommendedConfidenceLevel: recommended?.smartConfidenceLevel ?? "none",
  };
}

async function persist(snapshot: DarwishGroupMatchingFeedbackSnapshot) {
  const db = await getDb();
  if (!db) throw new Error("Database unavailable");
  await db.execute(sql`
    INSERT INTO darwish_group_matching_feedback (
      client_id, actor_user_id, decision_type,
      selected_group_jid, selected_evolution_instance,
      recommendation_available, recommended_group_jid, recommended_evolution_instance,
      selected_is_recommended, selected_confidence, selected_confidence_level, selected_signals,
      recommended_confidence, recommended_confidence_level
    ) VALUES (
      ${snapshot.clientId}, ${snapshot.actorUserId}, ${snapshot.decisionType},
      ${snapshot.selectedGroupJid}, ${snapshot.selectedEvolutionInstance},
      ${snapshot.recommendationAvailable ? 1 : 0}, ${snapshot.recommendedGroupJid}, ${snapshot.recommendedEvolutionInstance},
      ${snapshot.selectedIsRecommended ? 1 : 0}, ${snapshot.selectedConfidence}, ${snapshot.selectedConfidenceLevel},
      ${JSON.stringify(snapshot.selectedSignals)}, ${snapshot.recommendedConfidence}, ${snapshot.recommendedConfidenceLevel}
    )
  `);
}

export async function recordDarwishGroupMatchingFeedbackSafely(input: {
  clientId: number;
  actorUserId: number;
  selectedGroupJid: string;
  selectedEvolutionInstance: string;
  jobs: GroupJob[];
  linksBefore: GroupLink[];
}) {
  try {
    const candidates = __buildDarwishGroupCandidatesForFeedbackTests({
      clientId: input.clientId,
      jobs: input.jobs,
      linksBefore: input.linksBefore,
    });
    const rankedCandidates = await rankDarwishGroupCandidatesForClient({
      clientId: input.clientId,
      candidates,
      jobs: input.jobs,
    });
    const snapshot = __buildDarwishGroupMatchingFeedbackSnapshotForTests({
      clientId: input.clientId,
      actorUserId: input.actorUserId,
      selectedGroupJid: input.selectedGroupJid,
      selectedEvolutionInstance: input.selectedEvolutionInstance,
      rankedCandidates,
    });
    await persist(snapshot);
    return { recorded: true as const, decisionType: snapshot.decisionType };
  } catch (error) {
    console.warn("[DarwishGroupMatchingFeedback] audit write skipped", {
      clientId: Number(input.clientId) || null,
      actorUserId: Number(input.actorUserId) || null,
      errorClass: error instanceof Error ? error.name : "UnknownError",
    });
    return { recorded: false as const, decisionType: null };
  }
}
