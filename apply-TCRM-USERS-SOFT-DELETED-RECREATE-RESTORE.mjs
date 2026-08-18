import fs from "node:fs";

const file = "server/routers.ts";
const source = fs.readFileSync(file, "utf8");
const patchMarker = 'source: "routers.users.create.restore_soft_deleted"';

if (source.includes(patchMarker)) {
  console.log("PATCH_ALREADY_APPLIED");
  process.exit(0);
}

const startMarker = "        const existing = await getUserByEmail(normalizedEmail);";
const createMarker = "        const user = await createUser({";
const roleMarker = "          role: input.role,";
const conflictMarker = 'throw new TRPCError({ code: "CONFLICT", message: "Email already registered" });';
const endMarker = "        // Auto-grant bd_rep access when role is BusinessDeveloper";

function allIndexesOf(text, marker) {
  const out = [];
  let from = 0;
  while (true) {
    const index = text.indexOf(marker, from);
    if (index === -1) break;
    out.push(index);
    from = index + marker.length;
  }
  return out;
}

const targets = [];
for (const end of allIndexesOf(source, endMarker)) {
  const create = source.lastIndexOf(createMarker, end);
  if (create === -1) continue;
  const start = source.lastIndexOf(startMarker, create);
  if (start === -1) continue;

  const candidate = source.slice(start, end);
  const createCount = (candidate.match(/const user = await createUser\(/g) || []).length;
  if (
    createCount === 1 &&
    candidate.includes(roleMarker) &&
    candidate.includes(conflictMarker)
  ) {
    targets.push({ start, end });
  }
}

const uniqueTargets = targets.filter(
  (target, index, list) =>
    list.findIndex((other) => other.start === target.start && other.end === target.end) === index,
);

if (uniqueTargets.length === 0) {
  console.error("PATCH_TARGET_NOT_FOUND: admin users.create block was not found in the expected shape");
  process.exit(2);
}
if (uniqueTargets.length !== 1) {
  console.error(`PATCH_TARGET_AMBIGUOUS: expected exactly one admin users.create block, found ${uniqueTargets.length}`);
  process.exit(3);
}

const { start, end } = uniqueTargets[0];
const candidate = source.slice(start, end);

if (!candidate.includes("role: input.role")) {
  console.error("PATCH_TARGET_INVALID: selected block is not the admin role-aware create flow");
  process.exit(4);
}

const replacement = `        const existing = await getUserByEmail(normalizedEmail);\n        const softDeletedExisting = existing?.deletedAt ? existing : null;\n        if (existing && !softDeletedExisting) {\n          throw new TRPCError({ code: "CONFLICT", message: "Email already registered" });\n        }\n        const identity = await assertCentralIdentityUnique(input, softDeletedExisting?.id);\n        const passwordHash = await bcrypt.hash(input.password, 12);\n        let user;\n        if (softDeletedExisting) {\n          await updateUser(\n            Number(softDeletedExisting.id),\n            {\n              name: input.name,\n              email: normalizedEmail,\n              loginMethod: "email",\n              role: input.role,\n              passwordHash,\n              lastSignedIn: new Date(),\n              sessionVersion: Number(softDeletedExisting.sessionVersion ?? 1) + 1,\n              ...identity,\n              hrSyncStatus: identity.centralEmail && identity.centralId && (identity.nationalId || identity.passportNumber) ? "UNLINKED" : "MISSING_DATA",\n            } as any,\n            { actorUserId: ctx.user.id, source: "routers.users.create.restore_soft_deleted" },\n          );\n          await restoreUser(Number(softDeletedExisting.id));\n          user = await getUserByEmail(normalizedEmail);\n          if (!user || user.deletedAt) {\n            throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Failed to restore existing user" });\n          }\n        } else {\n          const openId = "local_" + nanoid(16);\n          user = await createUser({\n            openId,\n            name: input.name,\n            email: normalizedEmail,\n            loginMethod: "email",\n            role: input.role,\n            passwordHash,\n            lastSignedIn: new Date(),\n            ...identity,\n            hrSyncStatus: identity.centralEmail && identity.centralId && (identity.nationalId || identity.passportNumber) ? "UNLINKED" : "MISSING_DATA",\n          } as any);\n        }\n`;

const updated = source.slice(0, start) + replacement + source.slice(end);
if (updated === source) {
  console.error("PATCH_NO_CHANGE");
  process.exit(5);
}

fs.writeFileSync(file, updated, "utf8");
console.log("PATCH_APPLIED");
console.log(file);
