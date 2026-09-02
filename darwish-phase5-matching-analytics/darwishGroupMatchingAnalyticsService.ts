import { sql } from "drizzle-orm";
import { getDb } from "../../../db";

export type DarwishMatchingAnalyticsDays = 7 | 30 | 90;

type FeedbackRow = {
  decisionType?: unknown;
  selectedConfidence?: unknown;
  selectedSignals?: unknown;
  recommendedConfidence?: unknown;
  recommendedConfidenceLevel?: unknown;
  decisionDate?: unknown;
};

const DECISIONS = new Set(["accepted_recommendation", "overrode_recommendation", "manual_without_recommendation"]);
const LEVELS = ["high", "medium", "low", "none"] as const;
const SIGNALS = new Set(["exact_phone", "name", "business_name", "group_name", "participant_name", "sender_identity", "message_context", "other"]);

function rowsOf(result: any): any[] {
  if (Array.isArray(result) && Array.isArray(result[0])) return result[0];
  return Array.isArray(result) ? result : [];
}
function pct(n: number, d: number) { return d ? Math.round((n / d) * 1000) / 10 : 0; }
function num(value: unknown) {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}
function avg(values: Array<number | null>) {
  const valid = values.filter((v): v is number => v != null);
  return valid.length ? Math.round((valid.reduce((a, b) => a + b, 0) / valid.length) * 10) / 10 : null;
}
function level(value: unknown) {
  const text = String(value || "").trim().toLowerCase();
  return LEVELS.includes(text as any) ? text as typeof LEVELS[number] : "none";
}
function signals(value: unknown) {
  let parsed = value;
  if (typeof parsed === "string") { try { parsed = JSON.parse(parsed); } catch { parsed = []; } }
  if (!Array.isArray(parsed)) return [];
  return [...new Set(parsed.map((x) => String(x || "").trim()).filter((x) => SIGNALS.has(x)))];
}
function dateOnly(value: unknown) {
  const text = String(value || "").trim();
  return /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : null;
}

export function __buildDarwishMatchingAnalyticsForTests(input: {
  days: DarwishMatchingAnalyticsDays;
  rows: FeedbackRow[];
  available?: boolean;
  unavailableReason?: string | null;
  capped?: boolean;
}) {
  const rows = (input.rows || []).filter((row) => DECISIONS.has(String(row.decisionType || "")));
  const accepted = rows.filter((row) => row.decisionType === "accepted_recommendation");
  const overridden = rows.filter((row) => row.decisionType === "overrode_recommendation");
  const manual = rows.filter((row) => row.decisionType === "manual_without_recommendation");
  const recommended = [...accepted, ...overridden];

  const confidence = LEVELS.map((name) => {
    const bucket = recommended.filter((row) => level(row.recommendedConfidenceLevel) === name);
    const bucketAccepted = bucket.filter((row) => row.decisionType === "accepted_recommendation").length;
    return {
      level: name,
      decisions: bucket.length,
      accepted: bucketAccepted,
      overridden: bucket.length - bucketAccepted,
      acceptanceRatePct: pct(bucketAccepted, bucket.length),
    };
  });

  const signalCounts = new Map<string, number>();
  rows.forEach((row) => signals(row.selectedSignals).forEach((signal) => signalCounts.set(signal, (signalCounts.get(signal) || 0) + 1)));
  const selectedSignalUsage = [...signalCounts.entries()]
    .map(([signal, count]) => ({ signal, count, sharePct: pct(count, rows.length) }))
    .sort((a, b) => b.count - a.count || a.signal.localeCompare(b.signal));

  const trend = new Map<string, { date: string; total: number; accepted: number; overridden: number; manual: number }>();
  rows.forEach((row) => {
    const date = dateOnly(row.decisionDate);
    if (!date) return;
    const item = trend.get(date) || { date, total: 0, accepted: 0, overridden: 0, manual: 0 };
    item.total += 1;
    if (row.decisionType === "accepted_recommendation") item.accepted += 1;
    else if (row.decisionType === "overrode_recommendation") item.overridden += 1;
    else item.manual += 1;
    trend.set(date, item);
  });

  return {
    available: input.available ?? true,
    unavailableReason: input.unavailableReason ?? null,
    days: input.days,
    capped: Boolean(input.capped),
    summary: {
      totalDecisions: rows.length,
      recommendationDecisions: recommended.length,
      acceptedRecommendations: accepted.length,
      overrodeRecommendations: overridden.length,
      manualWithoutRecommendation: manual.length,
      recommendationCoveragePct: pct(recommended.length, rows.length),
      acceptanceRatePct: pct(accepted.length, recommended.length),
      overrideRatePct: pct(overridden.length, recommended.length),
      averageRecommendedConfidence: avg(recommended.map((row) => num(row.recommendedConfidence))),
      averageSelectedConfidence: avg(rows.map((row) => num(row.selectedConfidence))),
    },
    confidence,
    selectedSignalUsage,
    dailyTrend: [...trend.values()].sort((a, b) => a.date.localeCompare(b.date)).map((item) => ({
      ...item,
      acceptanceRatePct: pct(item.accepted, item.accepted + item.overridden),
    })),
  };
}

function unavailable(days: DarwishMatchingAnalyticsDays, reason: string) {
  return __buildDarwishMatchingAnalyticsForTests({ days, rows: [], available: false, unavailableReason: reason });
}

export async function getDarwishGroupMatchingAnalytics(days: DarwishMatchingAnalyticsDays = 30) {
  const db = await getDb();
  if (!db) return unavailable(days, "database_unavailable");
  const since = new Date(Date.now() - days * 86400000);
  try {
    const rows = rowsOf(await db.execute(sql`
      SELECT
        decision_type AS decisionType,
        selected_confidence AS selectedConfidence,
        selected_signals AS selectedSignals,
        recommended_confidence AS recommendedConfidence,
        recommended_confidence_level AS recommendedConfidenceLevel,
        DATE_FORMAT(created_at, '%Y-%m-%d') AS decisionDate
      FROM darwish_group_matching_feedback
      WHERE created_at >= ${since}
      ORDER BY created_at ASC
      LIMIT 10000
    `));
    return __buildDarwishMatchingAnalyticsForTests({ days, rows, capped: rows.length >= 10000 });
  } catch (error) {
    console.warn("[DarwishMatchingAnalytics] read unavailable", {
      days,
      errorClass: error instanceof Error ? error.name : "UnknownError",
    });
    return unavailable(days, "feedback_data_unavailable");
  }
}
