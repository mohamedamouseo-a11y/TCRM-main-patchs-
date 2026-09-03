import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { permissionProcedure, router } from "./_core/trpc";
import { PERMISSION_SCOPES } from "./security/permissionCatalog";
import {
  PermissionAdminError,
  createPermissionRole,
  deletePermissionRole,
  duplicatePermissionRole,
  getPermissionCatalogForAdmin,
  getPermissionRole,
  listPermissionRoles,
  replacePermissionRolePermissions,
  setPermissionRoleActive,
  updatePermissionRole,
} from "./security/permissionAdminService";

function actorId(ctx: any) {
  const id = Number(ctx.user?.id);
  if (!Number.isFinite(id) || id <= 0) throw new TRPCError({ code: "UNAUTHORIZED" });
  return id;
}

function mapError(error: unknown): never {
  if (error instanceof TRPCError) throw error;
  if (error instanceof PermissionAdminError) {
    const code = error.code === "NOT_FOUND" ? "NOT_FOUND"
      : error.code === "CONFLICT" ? "CONFLICT"
      : error.code === "FORBIDDEN" ? "FORBIDDEN"
      : "BAD_REQUEST";
    throw new TRPCError({ code, message: error.message });
  }
  throw error;
}

const roleIdInput = z.object({ roleId: z.number().int().positive() });
const roleDetailsInput = z.object({
  name: z.string().trim().min(2).max(150),
  nameAr: z.string().trim().max(150).optional().nullable(),
  description: z.string().trim().max(2000).optional().nullable(),
});

export const permissionsAdminRouter = router({
  catalog: permissionProcedure("roles.view").query(async () => getPermissionCatalogForAdmin()),
  listRoles: permissionProcedure("roles.view").query(async () => listPermissionRoles()),
  getRole: permissionProcedure("roles.view")
    .input(roleIdInput)
    .query(async ({ input }) => getPermissionRole(input.roleId)),

  createRole: permissionProcedure("roles.create")
    .input(roleDetailsInput.extend({ roleKey: z.string().trim().min(2).max(100).optional() }))
    .mutation(async ({ ctx, input }) => {
      try { return await createPermissionRole(input, actorId(ctx)); } catch (error) { return mapError(error); }
    }),

  updateRole: permissionProcedure("roles.edit")
    .input(roleDetailsInput.extend({ roleId: z.number().int().positive() }))
    .mutation(async ({ ctx, input }) => {
      try {
        return await updatePermissionRole(input.roleId, {
          name: input.name,
          nameAr: input.nameAr,
          description: input.description,
        }, actorId(ctx));
      } catch (error) { return mapError(error); }
    }),

  duplicateRole: permissionProcedure("roles.create")
    .input(z.object({
      sourceRoleId: z.number().int().positive(),
      roleKey: z.string().trim().min(2).max(100).optional(),
      name: z.string().trim().min(2).max(150),
      nameAr: z.string().trim().max(150).optional().nullable(),
    }))
    .mutation(async ({ ctx, input }) => {
      try { return await duplicatePermissionRole(input.sourceRoleId, input, actorId(ctx)); } catch (error) { return mapError(error); }
    }),

  replacePermissions: permissionProcedure("roles.assign_permissions")
    .input(z.object({
      roleId: z.number().int().positive(),
      entries: z.array(z.object({
        permissionKey: z.string().min(3).max(190),
        effect: z.enum(["allow", "deny"]),
        dataScope: z.enum(PERMISSION_SCOPES),
        scopeConfig: z.record(z.string(), z.unknown()).optional().nullable(),
      })).max(250),
    }))
    .mutation(async ({ ctx, input }) => {
      try { return await replacePermissionRolePermissions(input.roleId, input.entries as any, actorId(ctx)); } catch (error) { return mapError(error); }
    }),

  setActive: permissionProcedure("roles.edit")
    .input(roleIdInput.extend({ isActive: z.boolean() }))
    .mutation(async ({ ctx, input }) => {
      try { return await setPermissionRoleActive(input.roleId, input.isActive, actorId(ctx)); } catch (error) { return mapError(error); }
    }),

  deleteRole: permissionProcedure("roles.delete")
    .input(roleIdInput)
    .mutation(async ({ ctx, input }) => {
      try { return await deletePermissionRole(input.roleId, actorId(ctx)); } catch (error) { return mapError(error); }
    }),
});
