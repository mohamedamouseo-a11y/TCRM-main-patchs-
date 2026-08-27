import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { ACCESS_EFFECTS, ACCESS_PERMISSION_REGISTRY, ACCESS_SCOPES } from "@shared/accessControl";
import { adminProcedure, protectedProcedure, router } from "./_core/trpc";
import { checkAccess } from "./services/accessControl/accessEngine";
import {
  assignAccessRole,
  createAccessRole,
  createTemporaryAccessGrant,
  getAccessControlOverview,
  getAccessRolePermissions,
  isAccessControlInstalled,
  listAccessRoles,
  setAccessRolePermission,
  upsertAccessUserOverride,
} from "./services/accessControl/accessStore";

const effectSchema = z.enum(ACCESS_EFFECTS);
const scopeSchema = z.enum(ACCESS_SCOPES);
const conditionSchema = z.object({
  left: z.string().min(1).max(120),
  operator: z.enum(["eq", "neq", "in", "not_in", "lt", "lte", "gt", "gte", "exists"]),
  right: z.unknown().optional(),
}).strict();

function rethrow(error: unknown): never {
  if ((error as any)?.code === "ACCESS_CONTROL_NOT_READY") {
    throw new TRPCError({
      code: "PRECONDITION_FAILED",
      message: "Access Control migration is required before using this feature",
    });
  }
  throw error;
}

export const accessControlRouter = router({
  status: protectedProcedure.query(async () => ({
    installed: await isAccessControlInstalled(),
    mode: "shadow" as const,
  })),

  check: protectedProcedure
    .input(z.object({
      permission: z.string().min(3).max(160),
      resourceType: z.string().max(80).optional().nullable(),
      resourceId: z.union([z.string(), z.number()]).optional().nullable(),
      resource: z.record(z.string(), z.unknown()).optional().nullable(),
      context: z.record(z.string(), z.unknown()).optional().nullable(),
    }).strict())
    .query(({ ctx, input }) => checkAccess({
      user: ctx.user as any,
      ...input,
      logDecision: false,
    })),

  registry: adminProcedure.query(() => ACCESS_PERMISSION_REGISTRY),

  overview: adminProcedure.query(async () => {
    try { return await getAccessControlOverview(); } catch (error) { return rethrow(error); }
  }),

  roles: adminProcedure.query(async () => {
    try { return await listAccessRoles(); } catch (error) { return rethrow(error); }
  }),

  rolePermissions: adminProcedure
    .input(z.object({ roleId: z.number().int().positive() }).strict())
    .query(async ({ input }) => {
      try { return await getAccessRolePermissions(input.roleId); } catch (error) { return rethrow(error); }
    }),

  createRole: adminProcedure
    .input(z.object({
      roleKey: z.string().trim().regex(/^[A-Za-z][A-Za-z0-9_-]{2,63}$/),
      name: z.string().trim().min(2).max(120),
      description: z.string().trim().max(500).optional().nullable(),
    }).strict())
    .mutation(async ({ ctx, input }) => {
      try { return await createAccessRole({ ...input, actorUserId: Number(ctx.user.id) }); }
      catch (error) { return rethrow(error); }
    }),

  setRolePermission: adminProcedure
    .input(z.object({
      roleId: z.number().int().positive(),
      permissionKey: z.string().min(3).max(160),
      effect: effectSchema,
      scope: scopeSchema,
      conditions: z.array(conditionSchema).max(12).optional().nullable(),
    }).strict())
    .mutation(async ({ input }) => {
      try { return await setAccessRolePermission(input); } catch (error) { return rethrow(error); }
    }),

  assignRole: adminProcedure
    .input(z.object({
      userId: z.number().int().positive(),
      roleId: z.number().int().positive(),
      validFrom: z.coerce.date().optional().nullable(),
      validTo: z.coerce.date().optional().nullable(),
    }).strict())
    .mutation(async ({ ctx, input }) => {
      if (input.validFrom && input.validTo && input.validTo <= input.validFrom) {
        throw new TRPCError({ code: "BAD_REQUEST", message: "validTo must be after validFrom" });
      }
      try { return await assignAccessRole({ ...input, actorUserId: Number(ctx.user.id) }); }
      catch (error) { return rethrow(error); }
    }),

  setUserOverride: adminProcedure
    .input(z.object({
      userId: z.number().int().positive(),
      permissionKey: z.string().min(3).max(160),
      effect: effectSchema,
      scope: scopeSchema,
      conditions: z.array(conditionSchema).max(12).optional().nullable(),
      reason: z.string().trim().max(500).optional().nullable(),
      expiresAt: z.coerce.date().optional().nullable(),
    }).strict())
    .mutation(async ({ ctx, input }) => {
      try { return await upsertAccessUserOverride({ ...input, actorUserId: Number(ctx.user.id) }); }
      catch (error) { return rethrow(error); }
    }),

  grantTemporary: adminProcedure
    .input(z.object({
      userId: z.number().int().positive(),
      permissionKey: z.string().min(3).max(160),
      scope: scopeSchema,
      conditions: z.array(conditionSchema).max(12).optional().nullable(),
      startsAt: z.coerce.date(),
      expiresAt: z.coerce.date(),
      reason: z.string().trim().min(3).max(500),
    }).strict())
    .mutation(async ({ ctx, input }) => {
      if (input.expiresAt <= input.startsAt) {
        throw new TRPCError({ code: "BAD_REQUEST", message: "expiresAt must be after startsAt" });
      }
      try { return await createTemporaryAccessGrant({ ...input, actorUserId: Number(ctx.user.id) }); }
      catch (error) { return rethrow(error); }
    }),

  simulate: adminProcedure
    .input(z.object({
      user: z.object({
        id: z.number().int().positive(),
        role: z.string().max(80).optional().nullable(),
        teamId: z.number().int().positive().optional().nullable(),
        email: z.string().email().optional().nullable(),
      }).passthrough(),
      permission: z.string().min(3).max(160),
      resourceType: z.string().max(80).optional().nullable(),
      resourceId: z.union([z.string(), z.number()]).optional().nullable(),
      resource: z.record(z.string(), z.unknown()).optional().nullable(),
      context: z.record(z.string(), z.unknown()).optional().nullable(),
    }).strict())
    .query(({ input }) => checkAccess({ ...input, user: input.user as any, logDecision: true })),
});
