# Darwish WhatsApp Group → Client Linking — Phase 1

Base: `ebaf60b14578753148ec8fc20aa3d88cc380a408`

## Purpose
Expose the existing deterministic `darwish_group_links` relationship on the client profile and surface the latest known Chatwoot conversation id/activity for each linked WhatsApp group.

## Scope
- Read linked groups by exact `client_id` from the existing `darwish_group_links` table.
- Preserve exact `group_jid + evolution_instance` identity; no AI inference.
- Include the latest known `chatwoot_conversation_id` and activity timestamp from matching `darwish_group_jobs` rows.
- Add `whatsappGroups` to the existing `accountManagement.getClientProfile` response after its existing access checks.
- Show every enabled linked group in a read-only Client Profile card.
- Support multiple groups per client and a clean empty state.
- Add a targeted pure helper/unit test for exact client isolation, disabled-link exclusion, and fail-closed invalid client ids.

## Explicitly excluded
- No automatic group→client creation or remapping.
- No fuzzy/name/LLM matching.
- No migration or database seed.
- No Response Rate, Response Time, Response Cycles, SLA, or dashboard.
- No outbound WhatsApp/Chatwoot messages.
- No CRM or assignment mutations.
- No deployment or TCRM main push in this artifact step.

## Validation performed on the artifact
- Unified patch structural apply check: PASS against an equivalent synthetic baseline.
- `git diff --check`: PASS.
- New TS/TSX and mapping addition syntax parse: PASS.
- Production/server runtime test: NOT EXECUTED; reserved for the next step after applying the patch.
