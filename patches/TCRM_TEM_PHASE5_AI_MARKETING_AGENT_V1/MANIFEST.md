# TCRM TEM Phase 5 — AI Marketing Agent V1

## Purpose

Adds a human-supervised AI Marketing Agent on top of TEM/Mautic. The agent can analyze aggregate CRM/TEM context, generate campaign proposals, require explicit human approval, and materialize only **draft** TEM assets. It has no send endpoint and cannot activate workers, SMTP, or production campaign delivery.

## Target

- TCRM checkout: `/var/www/TCRM-MAIN`
- Existing TEM route: `/tem`
- Existing TEM engine: Mautic 7.1.3
- Existing Phase 4 safety boundary must remain in place.
- Works on the **current server branch/worktree**; no branch switch, pull, reset, rebase, or GitHub push.

## Added files

- `server/tem/temAiPolicy.ts`
- `server/tem/temAiRouter.ts`
- `server/tem/temAiPolicy.test.ts`
- `client/src/pages/BD/TEMAIAgent.tsx`
- `drizzle/schema_tem_ai.ts`
- `drizzle/migrations/20260823_tem_ai_marketing_agent.sql`
- `scripts/apply-tem-ai-phase5-migration.ts`

## Modified files

- `server/tem/temRouter.ts` — registers `tem.ai`
- `client/src/pages/BD/TEMCenter.tsx` — adds the AI Agent tab

## Safety model

1. **No send capability** exists in the Phase 5 router.
2. AI generation uses aggregate CRM/TEM context; emails and phone-like strings in free text are redacted before provider calls.
3. Provider access is fail-closed and OpenAI-compatible:
   - `TEM_AI_ENABLED=YES`
   - `TEM_AI_BASE_URL`
   - `TEM_AI_API_KEY`
   - `TEM_AI_MODEL`
   - optional `TEM_AI_ALLOWED_HOSTS`
4. Provider base URL must be HTTPS, except localhost/127.0.0.1, and the hostname must be explicitly allowed.
5. Proposal approval is restricted to Admin/SalesManager and requires an explicit confirmation phrase.
6. Draft materialization is separately gated by `TEM_AI_DRAFT_MATERIALIZATION_ENABLED=YES` and an explicit confirmation phrase.
7. Materialization creates only unpublished Mautic/TEM email and campaign drafts. It does not publish, schedule, send, enable SMTP, or start workers.
8. Legacy Email Marketing data and Phase 4 controls are untouched.
9. Developer-role production mutations remain blocked.
10. Audit rows store action metadata/hashes, not provider keys or SMTP secrets.

## Database

Two additive tables:

- `tem_ai_proposals`
- `tem_ai_audit_events`

Migration is idempotent and non-destructive. `APPLY.sh` requires `TEM_PHASE5_APPLY_DB=YES` to apply it. Before setting that flag, Manus must create and verify a current TCRM DB backup.

## Apply

From the patch repository:

```bash
TCRM_DB_BACKUP_VERIFIED=YES TEM_PHASE5_APPLY_DB=YES \
bash patches/TCRM_TEM_PHASE5_AI_MARKETING_AGENT_V1/APPLY.sh
```

No AI provider key is required to install/build Phase 5. If not configured, the UI reports the provider as not configured and remains fail-closed.

## Optional runtime configuration

Keep secrets outside Git, for example in `/etc/tcrm-tem/tem.env`:

```text
TEM_AI_ENABLED=YES
TEM_AI_BASE_URL=https://api.openai.com/v1
TEM_AI_API_KEY=<runtime secret>
TEM_AI_MODEL=<approved model>
TEM_AI_ALLOWED_HOSTS=api.openai.com
TEM_AI_DRAFT_MATERIALIZATION_ENABLED=YES
```

## Success marker

```text
FINAL_MARKER=TCRM_TEM_PHASE5_AI_MARKETING_AGENT_V1_OK
```

## Explicitly out of scope

- SMTP setup
- real email sending
- worker/scheduler activation
- automatic campaign publishing
- automatic bulk contact sync
- automatic DNC mutation
- bypassing Phase 4 approval gates
- GitHub push
