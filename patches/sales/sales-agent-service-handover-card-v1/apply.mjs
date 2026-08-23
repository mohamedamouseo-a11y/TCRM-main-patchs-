#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

/**
 * TCRM — Sales Agent Service Handover Card V1
 *
 * Fixes the Lead Profile converted-client lookup for SalesAgent/ColdSalesAgent
 * without granting client.read.full. Owning sales agents reuse the existing
 * workflow.read authorization relationship and receive only the three fields
 * required by the Lead Profile handover card.
 *
 * Scope: server/routers.ts only.
 */

const mode = process.argv[2] ?? '--check';
const cwd = process.cwd();
const target = path.resolve(cwd, 'server/routers.ts');
const PATCH_MARKER = 'TCRM_SALES_AGENT_SERVICE_HANDOVER_CARD_V1';

function fail(message, code = 1) {
  console.error(`[sales-agent-service-handover-card-v1] ${message}`);
  process.exit(code);
}

function info(message) {
  console.log(`[sales-agent-service-handover-card-v1] ${message}`);
}

if (!fs.existsSync(target)) fail(`target not found: ${target}`, 2);

const originalRaw = fs.readFileSync(target, 'utf8');
const usesCRLF = originalRaw.includes('\r\n');
let source = originalRaw.replace(/\r\n/g, '\n');

const oldBlock = `    getClientByLeadId: clientOpsProcedure
      .input(z.object({ leadId: z.number() }))
      .query(async ({ input, ctx }) => {
        const client = await getClientByLeadId(input.leadId);
        if (!client) return null;
        if (normalizeUserRole(ctx.user.role) === "SalesManager") {
          return getClientSummaryContext({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, Number((client as any).id));
        }
        await assertAccountManagementClientAccess(ctx, Number((client as any).id), "client.read.full");
        return client;
      }),`;

const newBlock = `    getClientByLeadId: clientOpsProcedure
      .input(z.object({ leadId: z.number() }))
      .query(async ({ input, ctx }) => {
        const client = await getClientByLeadId(input.leadId);
        if (!client) return null;

        const role = normalizeUserRole(ctx.user.role);
        if (role === "SalesManager") {
          return getClientSummaryContext({ id: Number(ctx.user.id), role, teamId: ctx.user.teamId }, Number((client as any).id));
        }

        // ${PATCH_MARKER}
        // Lead Profile needs only a narrow handover locator for an owning sales agent.
        // Reuse the already-established workflow.read owner authorization instead of
        // broadening client.read.full for SalesAgent/ColdSalesAgent globally.
        if (["SalesAgent", "ColdSalesAgent"].includes(role)) {
          await assertWorkflowOperationAllowed(
            { id: Number(ctx.user.id), role, teamId: ctx.user.teamId },
            Number((client as any).id),
            "workflow.read",
          );
          return {
            id: Number((client as any).id),
            handoverStatus: (client as any).handoverStatus ?? null,
            briefStatus: (client as any).briefStatus ?? null,
          };
        }

        await assertAccountManagementClientAccess(ctx, Number((client as any).id), "client.read.full");
        return client;
      }),`;

function isPatched(input) {
  return input.includes(PATCH_MARKER)
    && input.includes('["SalesAgent", "ColdSalesAgent"].includes(role)')
    && input.includes('"workflow.read"')
    && input.includes('handoverStatus: (client as any).handoverStatus ?? null')
    && input.includes('briefStatus: (client as any).briefStatus ?? null');
}

function validatePrerequisites(input) {
  if (!input.includes('getClientByLeadId: clientOpsProcedure')) fail('getClientByLeadId procedure not found');
  if (!input.includes('assertWorkflowOperationAllowed')) fail('assertWorkflowOperationAllowed is not available in server/routers.ts');
  if (!input.includes('normalizeUserRole')) fail('normalizeUserRole is not available in server/routers.ts');
  if (!isPatched(input) && !input.includes(oldBlock)) fail('expected unpatched getClientByLeadId block not found');
}

if (mode === '--check') {
  validatePrerequisites(source);
  info(isPatched(source) ? 'already patched' : 'ready to apply scoped Sales Agent service handover lookup fix');
  process.exit(0);
}

if (mode === '--apply') {
  validatePrerequisites(source);
  if (!isPatched(source)) source = source.replace(oldBlock, newBlock);
  if (!isPatched(source)) fail('patch did not reach expected source state');

  const output = usesCRLF ? source.replace(/\n/g, '\r\n') : source;
  fs.writeFileSync(target, output, 'utf8');
  info('applied scoped Sales Agent service handover lookup fix');
  process.exit(0);
}

if (mode === '--verify') {
  if (!isPatched(source)) fail('expected patch markers are missing');
  if (source.includes(oldBlock)) fail('old broad getClientByLeadId block is still present');
  info('verification passed');
  process.exit(0);
}

fail(`unknown mode: ${mode}`);
