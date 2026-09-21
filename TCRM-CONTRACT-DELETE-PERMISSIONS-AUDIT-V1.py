#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

PATCH_NAME = "TCRM_CONTRACT_DELETE_PERMISSIONS_AUDIT_V1"
EXPECTED_MAIN_COMMIT = "a359b82be80095e25af94ab7571f086778586d63"
EXPECTED_BLOBS = {
    "server/security/corePermissionPolicy.ts": "c25d7aa5a62bfeb24c969f0b4fe109bad7c0c808",
    "server/db.ts": "2f20157c21f29958bb1b2187e762291b8cdb6f09",
    "server/routers.ts": "2ecf69bc39784c5fd15f77ae50a78def316ebba3",
}
TARGETS = tuple(EXPECTED_BLOBS)
BACKUP_DIR = Path(".tcrm-patch-backups") / PATCH_NAME


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"ANCHOR_FAIL={label}:expected_1_found_{count}")
    return text.replace(old, new, 1)


def run_git_diff_check() -> None:
    proc = subprocess.run(
        ["git", "diff", "--check", "--", *TARGETS],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError("GIT_DIFF_CHECK_FAIL=" + proc.stdout.strip().replace("\n", " | "))


def restore_backups() -> None:
    for rel in TARGETS:
        src = BACKUP_DIR / rel
        dst = Path(rel)
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def main() -> int:
    root = Path.cwd()
    missing = [rel for rel in TARGETS if not (root / rel).is_file()]
    if missing:
        print("PATCH=FAIL")
        print("ERROR=MISSING_SOURCE:" + ",".join(missing))
        return 2

    # Extra semantic guards: delete UI already exists and contracts already support soft delete.
    client_profile = root / "client/src/pages/ClientProfile.tsx"
    schema_file = root / "drizzle/schema.ts"
    if not client_profile.is_file() or "trpc.accountManagement.deleteContract.useMutation" not in client_profile.read_text(encoding="utf-8"):
        print("PATCH=FAIL")
        print("ERROR=FRONTEND_DELETE_CALL_GUARD_FAILED")
        return 2
    schema_text = schema_file.read_text(encoding="utf-8") if schema_file.is_file() else ""
    contracts_start = schema_text.find('export const contracts = mysqlTable("contracts"')
    contracts_end = schema_text.find("export const salesContractHandoverCleanupQueue", contracts_start)
    contracts_schema = schema_text[contracts_start:contracts_end] if contracts_start >= 0 and contracts_end > contracts_start else ""
    if "deletedAt:" not in contracts_schema or "deletedBy:" not in contracts_schema:
        print("PATCH=FAIL")
        print("ERROR=CONTRACT_SOFT_DELETE_SCHEMA_GUARD_FAILED")
        return 2

    originals: dict[str, str] = {}
    for rel, expected in EXPECTED_BLOBS.items():
        raw = (root / rel).read_bytes()
        actual = git_blob_sha(raw)
        if actual != expected:
            print("PATCH=STOP")
            print(f"SOURCE_GUARD_FAIL={rel}")
            print(f"EXPECTED_BLOB={expected}")
            print(f"ACTUAL_BLOB={actual}")
            print("ERROR=SOURCE_CHANGED_DO_NOT_FORCE")
            return 3
        originals[rel] = raw.decode("utf-8")

    updated = dict(originals)

    updated["server/security/corePermissionPolicy.ts"] = replace_once(
        updated["server/security/corePermissionPolicy.ts"],
        '''  "createcontract",\n  "updatecontract",\n  "getassignedrenewalcontext",''',
        '''  "createcontract",\n  "updatecontract",\n  "deletecontract",\n  "getassignedrenewalcontext",''',
        "core_permission_deletecontract",
    )

    updated["server/db.ts"] = replace_once(
        updated["server/db.ts"],
        '''export async function updateContract(id: number, data: Partial<InsertContract>): Promise<void> {\n  const db = await getDb();\n  if (!db) return;\n  await db.update(contracts).set(data).where(eq(contracts.id, id));\n}\n\n// ─── Account Management: Service Packages''',
        '''export async function updateContract(id: number, data: Partial<InsertContract>): Promise<void> {\n  const db = await getDb();\n  if (!db) return;\n  await db.update(contracts).set(data).where(eq(contracts.id, id));\n}\n\nexport async function softDeleteContract(id: number, deletedByUserId: number): Promise<Contract> {\n  const db = await getDb();\n  if (!db) throw new Error("Database not available");\n  const [existing] = await db\n    .select()\n    .from(contracts)\n    .where(and(eq(contracts.id, id), isNull(contracts.deletedAt)))\n    .limit(1);\n  if (!existing) throw new Error("Contract not found");\n\n  const result = await db\n    .update(contracts)\n    .set({ deletedAt: new Date(), deletedBy: deletedByUserId } as any)\n    .where(and(eq(contracts.id, id), isNull(contracts.deletedAt)));\n  const affectedRows = Number((result as any)?.[0]?.affectedRows ?? (result as any)?.affectedRows ?? 0);\n  if (affectedRows !== 1) throw new Error("Contract delete conflict");\n  return existing as Contract;\n}\n\n// ─── Account Management: Service Packages''',
        "db_soft_delete_contract",
    )

    updated["server/routers.ts"] = replace_once(
        updated["server/routers.ts"],
        '''  getContractsByClient,\n  createContract,\n  updateContract,\n  getServicePackages,''',
        '''  getContractsByClient,\n  createContract,\n  updateContract,\n  softDeleteContract,\n  getServicePackages,''',
        "router_import_soft_delete_contract",
    )

    updated["server/routers.ts"] = replace_once(
        updated["server/routers.ts"],
        '''async function assertAccountManagementContractAccess(\n  ctx: any,\n  contractId: number,\n  operation: "contract.read.full" | "contract.read.renewal" | "contract.update" | "contract.delete" | "renewal.update" | "renewal.payment.create" = "contract.read.full",\n) {\n  await assertContractOperationAllowed({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, contractId, operation);\n  try {\n    return await getContractById(contractId);\n  } catch {\n    throw new TRPCError({ code: "NOT_FOUND", message: "Contract not found" });\n  }\n}\n\nfunction parseRequiredBusinessDate''',
        '''async function assertAccountManagementContractAccess(\n  ctx: any,\n  contractId: number,\n  operation: "contract.read.full" | "contract.read.renewal" | "contract.update" | "contract.delete" | "renewal.update" | "renewal.payment.create" = "contract.read.full",\n) {\n  await assertContractOperationAllowed({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, contractId, operation);\n  try {\n    return await getContractById(contractId);\n  } catch {\n    throw new TRPCError({ code: "NOT_FOUND", message: "Contract not found" });\n  }\n}\n\nfunction contractAuditSnapshot(contract: any) {\n  if (!contract) return null;\n  const auditText = (value: unknown, maxLength = 1000) =>\n    typeof value === "string" ? value.slice(0, maxLength) : (value ?? null);\n  return {\n    id: Number(contract.id),\n    clientId: Number(contract.clientId),\n    packageId: contract.packageId ?? null,\n    contractName: auditText(contract.contractName, 255),\n    startDate: contract.startDate ?? null,\n    endDate: contract.endDate ?? null,\n    period: auditText(contract.period, 100),\n    charges: contract.charges ?? null,\n    currency: auditText(contract.currency, 10),\n    monthlyCharges: contract.monthlyCharges ?? null,\n    status: contract.status ?? null,\n    contractRenewalStatus: contract.contractRenewalStatus ?? null,\n    renewalAssignedTo: contract.renewalAssignedTo ?? null,\n    priceOffer: auditText(contract.priceOffer),\n    upselling: auditText(contract.upselling),\n    notes: auditText(contract.notes),\n    contractLink: auditText(contract.contractLink),\n  };\n}\n\nfunction parseRequiredBusinessDate''',
        "router_contract_audit_snapshot",
    )

    updated["server/routers.ts"] = replace_once(
        updated["server/routers.ts"],
        '''        const id = await createContract(contractData);\n        let flow: Awaited<ReturnType<typeof syncClientBusinessFlow>> | null = null;''',
        '''        const id = await createContract(contractData);\n        if (!Number.isInteger(id) || id <= 0) {\n          throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Failed to create contract." });\n        }\n        const createdContract = (await getContractsByClient(input.clientId)).find((row: any) => Number(row.id) === Number(id));\n        await createAuditLog({\n          userId: Number(ctx.user.id),\n          userName: ctx.user.name ?? null,\n          userRole: String(ctx.user.role),\n          action: "create",\n          entityType: "contracts",\n          entityId: id,\n          entityName: String(createdContract?.contractName || input.contractName || `Contract #${id}`),\n          details: { clientId: input.clientId, source: "client_profile_contract" },\n          newValue: contractAuditSnapshot(createdContract ?? { ...contractData, id, clientId: input.clientId }),\n        });\n        let flow: Awaited<ReturnType<typeof syncClientBusinessFlow>> | null = null;''',
        "router_create_contract_audit",
    )

    updated["server/routers.ts"] = replace_once(
        updated["server/routers.ts"],
        '''        await updateContract(id, contractData);\n        const flow = await syncClientBusinessFlow(existing.clientId, { id: ctx.user.id, name: ctx.user.name ?? "Unknown", role: ctx.user.role });\n        return { success: true, flow };\n      }),\n\n\n\n\n    renewalCurrencyOptions:''',
        '''        const beforeContract = (await getContractsByClient(existing.clientId)).find((row: any) => Number(row.id) === Number(id));\n        if (!beforeContract) {\n          throw new TRPCError({ code: "NOT_FOUND", message: "Contract not found" });\n        }\n        await updateContract(id, contractData);\n        const afterContract = (await getContractsByClient(existing.clientId)).find((row: any) => Number(row.id) === Number(id));\n        if (!afterContract) {\n          throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Contract update could not be verified." });\n        }\n        await createAuditLog({\n          userId: Number(ctx.user.id),\n          userName: ctx.user.name ?? null,\n          userRole: String(ctx.user.role),\n          action: "update",\n          entityType: "contracts",\n          entityId: id,\n          entityName: String(afterContract.contractName || beforeContract.contractName || `Contract #${id}`),\n          details: {\n            clientId: existing.clientId,\n            source: "client_profile_contract",\n            changedFields: Object.keys(contractData),\n            contractFileChanged: Object.prototype.hasOwnProperty.call(contractData, "contractFile"),\n            before: contractAuditSnapshot(beforeContract),\n            after: contractAuditSnapshot(afterContract),\n          },\n          newValue: contractAuditSnapshot(afterContract),\n        });\n\n        let flow: Awaited<ReturnType<typeof syncClientBusinessFlow>> | null = null;\n        let flowWarning: string | null = null;\n        try {\n          flow = await syncClientBusinessFlow(existing.clientId, { id: ctx.user.id, name: ctx.user.name ?? "Unknown", role: ctx.user.role });\n        } catch (syncError: any) {\n          console.error(`[updateContract] syncClientBusinessFlow failed for client ${existing.clientId}:`, syncError instanceof Error ? syncError.message : String(syncError));\n          flowWarning = syncError instanceof Error ? syncError.message : String(syncError);\n        }\n        return { success: true, flow, warning: flowWarning };\n      }),\n\n    deleteContract: protectedProcedure\n      .input(z.object({ id: z.number().int().positive() }).strict())\n      .mutation(async ({ input, ctx }) => {\n        const access = await assertAccountManagementContractAccess(ctx, input.id, "contract.delete");\n        let deletedContract: any;\n        try {\n          deletedContract = await softDeleteContract(input.id, Number(ctx.user.id));\n        } catch (error: any) {\n          if (String(error?.message || "").includes("not found")) {\n            throw new TRPCError({ code: "NOT_FOUND", message: "Contract not found" });\n          }\n          if (String(error?.message || "").includes("conflict")) {\n            throw new TRPCError({ code: "CONFLICT", message: "Contract was already deleted or changed. Refresh and try again." });\n          }\n          throw error;\n        }\n\n        await createAuditLog({\n          userId: Number(ctx.user.id),\n          userName: ctx.user.name ?? null,\n          userRole: String(ctx.user.role),\n          action: "soft_delete",\n          entityType: "contracts",\n          entityId: input.id,\n          entityName: String(deletedContract.contractName || `Contract #${input.id}`),\n          details: {\n            clientId: Number(deletedContract.clientId || access.clientId),\n            source: "client_profile_contract",\n            status: deletedContract.status ?? null,\n            contractRenewalStatus: deletedContract.contractRenewalStatus ?? null,\n            beforeDeletion: {\n              deletedAt: deletedContract.deletedAt ?? null,\n              deletedBy: deletedContract.deletedBy ?? null,\n            },\n            contract: contractAuditSnapshot(deletedContract),\n          },\n          newValue: {\n            deleted: true,\n            deletedBy: Number(ctx.user.id),\n          },\n        });\n\n        let flow: Awaited<ReturnType<typeof syncClientBusinessFlow>> | null = null;\n        let flowWarning: string | null = null;\n        try {\n          flow = await syncClientBusinessFlow(Number(deletedContract.clientId || access.clientId), { id: ctx.user.id, name: ctx.user.name ?? "Unknown", role: ctx.user.role });\n        } catch (syncError: any) {\n          console.error(`[deleteContract] syncClientBusinessFlow failed for client ${deletedContract.clientId || access.clientId}:`, syncError instanceof Error ? syncError.message : String(syncError));\n          flowWarning = syncError instanceof Error ? syncError.message : String(syncError);\n        }\n        return { success: true, flow, warning: flowWarning };\n      }),\n\n\n\n\n    renewalCurrencyOptions:''',
        "router_update_delete_contract_audit",
    )

    # Verify patch output before touching the worktree.
    must_have = {
        "server/security/corePermissionPolicy.ts": ["\"deletecontract\""],
        "server/db.ts": ["export async function softDeleteContract"],
        "server/routers.ts": [
            "softDeleteContract,",
            "deleteContract: protectedProcedure",
            'assertAccountManagementContractAccess(ctx, input.id, "contract.delete")',
            'action: "soft_delete"',
            'entityType: "contracts"',
            '[updateContract] syncClientBusinessFlow failed',
        ],
    }
    for rel, markers in must_have.items():
        for marker in markers:
            if marker not in updated[rel]:
                raise RuntimeError(f"VERIFY_MARKER_FAIL={rel}:{marker}")

    # Contract audit records deliberately do NOT set top-level previousValue.
    # AuditLogPage treats previousValue as an automatic generic Undo trigger;
    # contract restore needs business-flow resync, so this patch avoids enabling
    # an unsafe restore path while still recording detailed before/after context.
    delete_block = updated["server/routers.ts"].split("deleteContract: protectedProcedure", 1)[1].split("renewalCurrencyOptions:", 1)[0]
    if "previousValue:" in delete_block:
        raise RuntimeError("VERIFY_FAIL=UNSAFE_GENERIC_CONTRACT_UNDO_ENABLED")

    # Back up only after every preflight/anchor/verification gate has passed.
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    for rel in TARGETS:
        src = root / rel
        dst = root / BACKUP_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    try:
        for rel in TARGETS:
            (root / rel).write_text(updated[rel], encoding="utf-8")
        run_git_diff_check()
    except Exception:
        restore_backups()
        raise

    print("PATCH=PASS")
    print("PATCH_NAME=" + PATCH_NAME)
    print("BASE_MAIN_COMMIT=" + EXPECTED_MAIN_COMMIT)
    print("FILES_CHANGED=" + ";".join(TARGETS))
    print("PERMISSION_GATE=contracts.delete")
    print("DELETE_MODE=SOFT_DELETE")
    print("AUDIT=create,update,soft_delete")
    print("AUDIT_GENERIC_UNDO=NOT_ENABLED_FOR_CONTRACT_ACTIONS")
    print("SYNC_FAILURE_AFTER_SAVE_OR_DELETE=NON_BLOCKING_WARNING")
    print("DB_MIGRATION=NO")
    print("BACKUP=" + str(BACKUP_DIR))
    print("GIT_DIFF_CHECK=PASS")
    print("ERROR=NONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("PATCH=FAIL")
        print("ERROR=" + str(exc).replace("\n", " | "))
        raise SystemExit(1)
