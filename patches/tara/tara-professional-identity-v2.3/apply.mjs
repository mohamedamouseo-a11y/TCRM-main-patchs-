#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * TCRM — Tara Professional Identity V2.3
 * Corrective frontend patch for partially-rendered/truncated portrait.
 * Replaces the portrait payload with a fresh verified baseline JPEG and
 * separates image clipping from the online-status badge.
 * No API, DB, routing, permissions, or Tara business-logic changes.
 */

const mode = process.argv[2] ?? '--check';
const cwd = process.cwd();
const target = path.resolve(cwd, 'client/src/pages/TaraAgentPage.tsx');
const patchDir = path.dirname(fileURLToPath(import.meta.url));
const avatarB64Path = path.join(patchDir, 'tara-avatar-160.jpg.b64');
const avatarTarget = path.resolve(cwd, 'client/src/assets/ai-staff/tara-avatar.jpg');

function fail(message, code = 1) {
  console.error(`[tara-identity-v2.3] ${message}`);
  process.exit(code);
}
function info(message) {
  console.log(`[tara-identity-v2.3] ${message}`);
}
function replaceOnce(input, before, after, label) {
  if (!input.includes(before)) fail(`expected block not found: ${label}`);
  return input.replace(before, after);
}
function decodeAvatar() {
  if (!fs.existsSync(avatarB64Path)) fail(`avatar payload not found: ${avatarB64Path}`);
  const raw = fs.readFileSync(avatarB64Path, 'utf8').trim();
  const buf = Buffer.from(raw, 'base64');
  if (buf.length !== 5816) fail(`unexpected avatar byte length: ${buf.length}`);
  if (buf[0] !== 0xff || buf[1] !== 0xd8) fail('avatar JPEG SOI marker missing');
  if (buf[buf.length - 2] !== 0xff || buf[buf.length - 1] !== 0xd9) fail('avatar JPEG EOI marker missing');
  return buf;
}

if (!fs.existsSync(target)) fail(`target not found: ${target}`, 2);
const originalRaw = fs.readFileSync(target, 'utf8');
const usesCRLF = originalRaw.includes('\r\n');
let source = originalRaw.replace(/\r\n/g, '\n');

const oldAvatarBlock = `            <div className="relative h-[76px] w-[76px] shrink-0 overflow-hidden rounded-[22px] bg-muted ring-4 ring-primary/10 shadow-lg shadow-primary/15">
              <img src={taraAvatar} alt={taraIdentity.alt} className="h-full w-full object-cover" />
              <span className={"absolute -bottom-1 -end-1 h-5 w-5 rounded-full border-[3px] border-card " + (settings.enabled ? "bg-emerald-500" : "bg-muted-foreground")} />
            </div>`;

const newAvatarBlock = `            <div className="relative h-[88px] w-[88px] shrink-0">
              <div className="h-full w-full overflow-hidden rounded-full border-2 border-background bg-card ring-4 ring-primary/10 shadow-lg shadow-primary/15">
                <img src={taraAvatar} alt={taraIdentity.alt} draggable={false} className="block h-full w-full object-cover object-[50%_22%]" />
              </div>
              <span className={"absolute bottom-0 end-0 h-5 w-5 rounded-full border-[3px] border-card shadow-sm " + (settings.enabled ? "bg-emerald-500" : "bg-muted-foreground")} />
            </div>`;

function isPatched(input) {
  return input.includes('h-[88px] w-[88px] shrink-0')
    && input.includes('rounded-full border-2 border-background')
    && input.includes('object-[50%_22%]')
    && input.includes('draggable={false}')
    && input.includes('src={taraAvatar}');
}

if (mode === '--check') {
  decodeAvatar();
  if (!source.includes('import taraAvatar from "@/assets/ai-staff/tara-avatar.jpg";')) fail('V2.2 taraAvatar import not found');
  if (!source.includes('AI Telesales & Lead Qualification Specialist')) fail('Tara professional identity markers not found');
  if (!isPatched(source) && !source.includes(oldAvatarBlock)) fail('expected V2.2 avatar block not found');
  info(isPatched(source) ? 'already patched' : 'ready to apply V2.3 portrait rendering fix');
  process.exit(0);
}

if (mode === '--apply') {
  const avatar = decodeAvatar();
  if (!isPatched(source)) {
    source = replaceOnce(source, oldAvatarBlock, newAvatarBlock, 'portrait layout');
  }
  fs.mkdirSync(path.dirname(avatarTarget), { recursive: true });
  fs.writeFileSync(avatarTarget, avatar);

  const written = fs.readFileSync(avatarTarget);
  if (written.length !== 5816 || written[0] !== 0xff || written[1] !== 0xd8 || written.at(-2) !== 0xff || written.at(-1) !== 0xd9) {
    fail('written avatar failed integrity validation');
  }
  if (!isPatched(source)) fail('portrait source markers missing after apply');

  const output = usesCRLF ? source.replace(/\n/g, '\r\n') : source;
  fs.writeFileSync(target, output, 'utf8');
  info('applied V2.3 portrait fix and replaced avatar with verified complete JPEG');
  process.exit(0);
}

if (mode === '--verify') {
  if (!isPatched(source)) fail('expected V2.3 portrait source markers are missing');
  if (!fs.existsSync(avatarTarget)) fail(`avatar missing: ${avatarTarget}`);
  const avatar = fs.readFileSync(avatarTarget);
  if (avatar.length !== 5816) fail(`avatar size mismatch: ${avatar.length}`);
  if (avatar[0] !== 0xff || avatar[1] !== 0xd8 || avatar.at(-2) !== 0xff || avatar.at(-1) !== 0xd9) fail('avatar JPEG markers invalid');
  info('verification passed');
  process.exit(0);
}

fail(`unknown mode: ${mode}`);
