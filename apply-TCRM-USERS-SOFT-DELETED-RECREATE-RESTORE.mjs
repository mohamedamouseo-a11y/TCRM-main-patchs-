import fs from "node:fs";

const file = "server/routers.ts";
const source = fs.readFileSync(file, "utf8");
const patchMarker = 'source: "routers.users.create.restore_soft_deleted"';

if (source.includes(patchMarker)) {
  console.log("PATCH_ALREADY_APPLIED");
  process.exit(0);
}

const startMarker = "        const existing = await getUserByEmail(normalizedEmail);";
const roleMarker = "          role: input.role,";
const endMarker = "        // Auto-grant bd_rep access when role is BusinessDeveloper";

let searchFrom = 0;
let start = -1;
let end = -1;
while (true) {
  const candidateStart = source.indexOf(startMarker, searchFrom);
  if (candidateStart === -1) break;
  const candidateEnd = source.indexOf(endMarker, candidateStart);
  if (candidateEnd === -1) break;
  const candidate = source.slice(candidateStart, candidateEnd);
  if (candidate.includes(roleMarker) && candidate.includes('throw new TRPCError({ code: "CONFLICT", message: "Email already registered" });')) {
    start = candidateStart;
    end = candidateEnd;
    break;
  }
  searchFrom = candidateStart + startMarker.length;
}

if (start === -1 || end === -1) {
  console.error("PATCH_TARGET_NOT_FOUND: admin users.create block was not found exactly once in expected shape");
  process.exit(2);
}

const candidate = source.slice(start, end);
const createCount = (candidate.match(/const user = await createUser\(/g) || []).length;
if (createCount !== 1) {
  console.error(`PATCH_TARGET_AMBIGUOUS: expected one admin createUser call, found ${createCount}`);
  process.exit(3);
}

const replacement = `        const existing = await getUserByEmail(normalizedEmail);\n        const softDeletedExisting = existing?.deletedAt ? existing : null;\n        if (existing && !softDeletedExisting) {\n          throw new TRPCError({ code: "CONFLICT", message: "Email already registered" });\n        }\n        const identity = await assertCentralIdentityUnique(input, softDeletedExisting?.id);\n        const passwordHash = await bcrypt.hash(input.password, 12);\n        let user;\n        if (softDeletedExisting) {\n          await updateUser(\n            Number(softDeletedExisting.id),\n            {\n              name: input.name,\n              email: normalizedEmail,\n              loginMethod: "email",\n              role: input.role,\n              passwordHash,\n              lastSignedIn: new Date(),\n              sessionVersion: Number(softDeletedExisting.sessionVersion ?? 1) + 1,\n              ...identity,\n              hrSyncStatus: identity.centralEmail && identity.centralId && (identity.nationalId || identity.passportNumber) ? "UNLINKED" : "MISSING_DATA",\n            } as any,\n            { actorUserId: ctx.user.id, source: "routers.users.create.restore_soft_deleted" },\n          );\n          await restoreUser(Number(softDeletedExisting.id));\n          user = await getUserByEmail(normalizedEmail);\n          if (!user || user.deletedAt) {\n            throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Failed to restore existing user" });\n          }\n        } else {\n          const openId = "local_" + nanoid(16);\n          user = await createUser({\n            openId,\n            name: input.name,\n            email: normalizedEmail,\n            loginMethod: "email",\n            role: input.role,\n            passwordHash,\n            lastSignedIn: new Date(),\n            ...identity,\n            hrSyncStatus: identity.centralEmail && identity.centralId && (identity.nationalId || identity.passportNumber) ? "UNLINKED" : "MISSING_DATA",\n          } as any);\n        }\n`;

const updated = source.slice(0, start) + replacement + source.slice(end);
if (updated === source) {
  console.error("PATCH_NO_CHANGE");
  process.exit(4);
}

fs.writeFileSync(file, updated, "utf8");
console.log("PATCH_APPLIED");
console.log(file);
