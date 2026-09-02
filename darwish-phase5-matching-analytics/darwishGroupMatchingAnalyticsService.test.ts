import { describe, expect, it } from "vitest";
import { __buildDarwishMatchingAnalyticsForTests } from "./darwishGroupMatchingAnalyticsService";

function row(overrides: Record<string, unknown> = {}) {
  return {
    decisionType: "accepted_recommendation",
    selectedConfidence: 91,
    selectedSignals: JSON.stringify(["exact_phone", "group_name"]),
    recommendedConfidence: 91,
    recommendedConfidenceLevel: "high",
    decisionDate: "2026-09-01",
    ...overrides,
  };
}

describe("Darwish matching analytics", () => {
  it("computes coverage, acceptance, override and manual rates from Phase 4 audit rows", () => {
    const result = __buildDarwishMatchingAnalyticsForTests({
      days: 30,
      rows: [
        row(),
        row({ recommendedConfidence: 88 }),
        row({ decisionType: "overrode_recommendation", selectedConfidence: 62, selectedSignals: JSON.stringify(["name"]), recommendedConfidence: 84 }),
        row({ decisionType: "manual_without_recommendation", recommendedConfidence: null, recommendedConfidenceLevel: "none" }),
      ],
    });
    expect(result.summary).toMatchObject({
      totalDecisions: 4, recommendationDecisions: 3, acceptedRecommendations: 2,
      overrodeRecommendations: 1, manualWithoutRecommendation: 1,
      recommendationCoveragePct: 75, acceptanceRatePct: 66.7, overrideRatePct: 33.3,
    });
  });

  it("measures confidence quality from the recommended candidate", () => {
    const result = __buildDarwishMatchingAnalyticsForTests({
      days: 30,
      rows: [row(), row({ decisionType: "overrode_recommendation" }), row({ decisionType: "overrode_recommendation", recommendedConfidenceLevel: "medium" })],
    });
    expect(result.confidence.find((x) => x.level === "high")).toMatchObject({ decisions: 2, accepted: 1, overridden: 1, acceptanceRatePct: 50 });
    expect(result.confidence.find((x) => x.level === "medium")).toMatchObject({ decisions: 1, accepted: 0, overridden: 1, acceptanceRatePct: 0 });
  });

  it("allow-lists signals and excludes unknown values", () => {
    const result = __buildDarwishMatchingAnalyticsForTests({
      days: 7,
      rows: [row({ selectedSignals: JSON.stringify(["exact_phone", "secret_signal", "exact_phone"]) }), row({ selectedSignals: ["name", "secret_signal"] })],
    });
    expect(result.selectedSignalUsage).toEqual([
      { signal: "exact_phone", count: 1, sharePct: 50 },
      { signal: "name", count: 1, sharePct: 50 },
    ]);
    expect(JSON.stringify(result)).not.toContain("secret_signal");
  });

  it("builds daily trends and ignores invalid decision types", () => {
    const result = __buildDarwishMatchingAnalyticsForTests({
      days: 90,
      rows: [row({ decisionDate: "2026-08-31" }), row({ decisionType: "overrode_recommendation", decisionDate: "2026-08-31" }), row({ decisionType: "manual_without_recommendation" }), row({ decisionType: "invented" })],
    });
    expect(result.summary.totalDecisions).toBe(3);
    expect(result.dailyTrend[0]).toEqual({ date: "2026-08-31", total: 2, accepted: 1, overridden: 1, manual: 0, acceptanceRatePct: 50 });
  });
});
