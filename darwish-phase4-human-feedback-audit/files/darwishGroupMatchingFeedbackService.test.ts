import { describe, expect, it } from "vitest";
import {
  __buildDarwishGroupCandidatesForFeedbackTests,
  __buildDarwishGroupMatchingFeedbackSnapshotForTests,
} from "./darwishGroupMatchingFeedbackService";
import type { DarwishSmartGroupCandidate } from "./darwishSmartGroupMatchingService";

function smartCandidate(overrides: Partial<DarwishSmartGroupCandidate> = {}): DarwishSmartGroupCandidate {
  return {
    groupJid: "120363000001@g.us",
    groupName: "Acme Marketing",
    evolutionInstance: "main",
    chatwootConversationId: null,
    lastActivityAt: null,
    linkedClientId: null,
    status: "unlinked",
    eligible: true,
    smartMatchStatus: "ranked",
    smartConfidence: 91,
    smartConfidenceLevel: "high",
    smartReasons: ["This free-text reason must never be persisted by Phase 4"],
    smartSignals: ["exact_phone", "group_name"],
    darwishRecommended: true,
    ...overrides,
  };
}

describe("Darwish smart group matching feedback audit", () => {
  it("classifies accepted recommendation and keeps free-text reasons out of the snapshot", () => {
    const snapshot = __buildDarwishGroupMatchingFeedbackSnapshotForTests({
      clientId: 118,
      actorUserId: 7,
      selectedGroupJid: "120363000001@g.us",
      selectedEvolutionInstance: "main",
      rankedCandidates: [smartCandidate()],
    });
    expect(snapshot.decisionType).toBe("accepted_recommendation");
    expect(snapshot.selectedIsRecommended).toBe(true);
    expect(snapshot.selectedConfidence).toBe(91);
    expect(snapshot.selectedSignals).toEqual(["exact_phone", "group_name"]);
    expect(snapshot).not.toHaveProperty("smartReasons");
    expect(snapshot).not.toHaveProperty("reasons");
  });

  it("classifies a human override when another real group was recommended", () => {
    const snapshot = __buildDarwishGroupMatchingFeedbackSnapshotForTests({
      clientId: 118,
      actorUserId: 7,
      selectedGroupJid: "120363000002@g.us",
      selectedEvolutionInstance: "main",
      rankedCandidates: [
        smartCandidate(),
        smartCandidate({
          groupJid: "120363000002@g.us",
          groupName: "Acme Ops",
          smartConfidence: 62,
          smartConfidenceLevel: "medium",
          smartSignals: ["name"],
          darwishRecommended: false,
        }),
      ],
    });
    expect(snapshot.decisionType).toBe("overrode_recommendation");
    expect(snapshot.selectedIsRecommended).toBe(false);
    expect(snapshot.recommendedGroupJid).toBe("120363000001@g.us");
    expect(snapshot.selectedConfidence).toBe(62);
  });

  it("classifies manual linking when there is no Darwish recommendation", () => {
    const snapshot = __buildDarwishGroupMatchingFeedbackSnapshotForTests({
      clientId: 118,
      actorUserId: 7,
      selectedGroupJid: "120363000001@g.us",
      selectedEvolutionInstance: "main",
      rankedCandidates: [smartCandidate({ darwishRecommended: false, smartConfidence: 52, smartConfidenceLevel: "low" })],
    });
    expect(snapshot.decisionType).toBe("manual_without_recommendation");
    expect(snapshot.recommendationAvailable).toBe(false);
    expect(snapshot.recommendedGroupJid).toBeNull();
  });

  it("keeps a group linked to another client ineligible in the pre-link snapshot", () => {
    const candidates = __buildDarwishGroupCandidatesForFeedbackTests({
      clientId: 118,
      jobs: [{ groupJid: "120363000099@g.us", groupName: "Blocked", evolutionInstance: "main" }],
      linksBefore: [{ clientId: 999, groupJid: "120363000099@g.us", evolutionInstance: "main", enabled: 1 }],
    });
    expect(candidates).toHaveLength(1);
    expect(candidates[0].status).toBe("linked_other");
    expect(candidates[0].eligible).toBe(false);
  });
});
