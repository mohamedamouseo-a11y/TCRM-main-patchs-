#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

/**
 * TCRM — Sales Agent Service Handover Card V1.1
 *
 * V1 correctly added a scoped workflow.read authorization branch, but the
 * enclosing clientOpsProcedure middleware rejects SalesAgent/ColdSalesAgent
 * before the handler can execute. V1.1 changes ONLY this one procedure to
 * protectedProcedure so its in-handler authorization can run.
 *
 * Scope: server/routers.ts only.
 */

const mode = process.argv[2] ?? '--check';
const cwd = process.cwd();
const target = path.resolve(cwd, 'server/routers.ts');
const V1_MARKER = 'TCRM_SALES_AGENT_SERVICE_HANDOVER_CARD_V1';
const V11_MARKER = 'TCRM_SALES_AGENT_SERVICE_HANDOVER_CARD_V1_1';

function fail(message, code = 1) {
  console.error(`[sales-agent-service-handover-card-v1.1] ${message}`);
  process.exit(code);
}
function info(message) {
  console.log(`[sales-agent-service-handover-card-v1.1] ${message}`);
}

if (!fs.existsSync(target)) fail(`target not found: ${target}`, 2);
const originalRaw = fs.readFileSync(target, 'utf8');
const usesCRLF = originalRaw.includes('\r\n');
let source = originalRaw.replace(/\r\n/g, '\n');

const originalBlock = `    getClientByLeadId: clientOpsProcedure
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

const finalBlock = `    // ${V11_MARKER}
    getClientByLeadId: protectedProcedure
      .input(z.object({ leadId: z.number() }))
      .query(async ({ input, ctx }) => {
        const client = await getClientByLeadId(input.leadId);
        if (!client) return null;

        const role = normalizeUserRole(ctx.user.role);
        if (role === "SalesManager") {
          return getClientSummaryContext({ id: Number(ctx.user.id), role, teamId: ctx.user.teamId }, Number((client as any).id));
        }

        // ${V1_MARKER}
        // Lead Profile needs only a narrow handover locator for an owning sales agent.
        // Reuse the existing workflow.read owner authorization instead of broadening
        // client.read.full/client.read.summary for SalesAgent/ColdSalesAgent.
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

function locateProcedureBlock(input) {
  const startCandidates = [
    input.indexOf(`    // ${V11_MARKER}\n    getClientByLeadId:`),
    input.indexOf('    getClientByLeadId: clientOpsProcedure'),
    input.indexOf('    getClientByLeadId: protectedProcedure'),
  ].filter((value) => value >= 0);
  if (!startCandidates.length) fail('getClientByLeadId procedure not found');
  const start = Math.min(...startCandidates);
  const nextProcedure = input.indexOf('\n\n    getClientProfile:', start);
  if (nextProcedure === -1) fail('getClientByLeadId end marker not found');
  return { start, end: nextProcedure };
}

function hasScopedBranch(input) {
  return input.includes(V1_MARKER)
    && input.includes('["SalesAgent", "ColdSalesAgent"].includes(role)')
    && input.includes('assertWorkflowOperationAllowed(')
    && input.includes('"workflow.read"')
    && input.includes('handoverStatus: (client as any).handoverStatus ?? null')
    && input.includes('briefStatus: (client as any).briefStatus ?? null');
}

function isPatched(input) {
  const { start, end } = locateProcedureBlock(input);
  const block = input.slice(start, end);
  return block.includes(V11_MARKER)
    && block.includes('getClientByLeadId: protectedProcedure')
    && !block.includes('getClientByLeadId: clientOpsProcedure')
    && hasScopedBranch(block);
}

function validatePrerequisites(input) {
  if (!input.includes('const clientOpsProcedure = protectedProcedure.use')) fail('clientOpsProcedure middleware definition not found');
  if (!input.includes('message: "Client read access required"')) fail('expected clientOps role gate not found');
  if (!input.includes('protectedProcedure')) fail('protectedProcedure is not available');
  if (!input.includes('assertWorkflowOperationAllowed')) fail('assertWorkflowOperationAllowed is not available');
  locateProcedureBlock(input);
}

if (mode === '--check') {
  validatePrerequisites(source);
  if (isPatched(source)) {
    info('already patched');
    process.exit(0);
  }
  const { start, end } = locateProcedureBlock(source);
  const block = source.slice(start, end);
  const acceptable = block.includes(originalBlock.trim()) || hasScopedBranch(block);
  if (!acceptable) fail('getClientByLeadId is neither original nor V1-compatible');
  info('ready to apply V1.1 middleware-gate correction');
  process.exit(0);
}

if (mode === '--apply') {
  validatePrerequisites(source);
  if (!isPatched(source)) {
    const { start, end } = locateProcedureBlock(source);
    source = source.slice(0, start) + finalBlock + source.slice(end);
  }
  if (!isPatched(source)) fail('patch did not reach expected V1.1 state');
  const output = usesCRLF ? source.replace(/\n/g, '\r\n') : source;
  fs.writeFileSync(target, output, 'utf8');
  info('applied V1.1: scoped lookup now bypasses clientOpsProcedure middleware and authorizes inside handler');
  process.exit(0);
}

if (mode === '--verify') {
  validatePrerequisites(source);
  if (!isPatched(source)) fail('expected V1.1 state is missing');
  const { start, end } = locateProcedureBlock(source);
  const block = source.slice(start, end);
  if (block.includes('clientOpsProcedure')) fail('getClientByLeadId still uses clientOpsProcedure');
  if (!block.includes('protectedProcedure')) fail('getClientByLeadId is not protectedProcedure');
  info('verification passed');
  process.exit(0);
}

fail(`unknown mode: ${mode}`);
