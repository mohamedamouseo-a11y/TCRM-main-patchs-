#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

required = [
    root / "shared/systemSmartSearch.ts",
    root / "shared/searchNormalization.ts",
    root / "client/src/components/search/SmartSearchBar.tsx",
    root / "scripts/audit-smart-search-bars.ts",
]
missing = [str(p.relative_to(root)) for p in required if not p.exists()]
if missing:
    raise SystemExit(
        "TFCRM parity patch requires completed Phase 6 working tree. Missing: "
        + ", ".join(missing)
    )

audit = subprocess.run(
    ["pnpm", "exec", "tsx", "scripts/audit-smart-search-bars.ts", "--strict"],
    cwd=root,
    text=True,
    capture_output=True,
)
if audit.returncode != 0:
    sys.stdout.write(audit.stdout)
    sys.stderr.write(audit.stderr)
    raise SystemExit(
        "Phase 6 strict audit is not green. Complete Phase 6 (Pending: 0) before TFCRM parity."
    )

parity_ts = r'''/**
 * TFCRM-parity search policy for TCRM.
 *
 * Deliberate parity rules:
 * - run normalized exact/partial matching across the authorized collection first
 * - use fuzzy matching only when the exact stage returns zero rows
 * - never fuzzy structured fields (phone/email/IDs/codes)
 * - keep fuzzy candidate evaluation bounded after authorization/scoping
 *
 * TCRM intentionally keeps its stronger Arabic normalization from
 * shared/searchNormalization.ts.
 */
import { normalizeSearchText } from "./searchNormalization";

export const TFCRM_PARITY_SUGGESTION_MIN_LENGTH = 2;
export const TFCRM_PARITY_SUGGESTION_LIMIT = 6;
export const TFCRM_PARITY_GLOBAL_CANDIDATE_LIMIT = 500;
export const TFCRM_PARITY_LIST_CANDIDATE_LIMIT = 1000;

const LETTER_RE = /[A-Za-z\u0600-\u06ff]/u;
const WORD_SPLIT_RE = /[\s,;|/\\()[\]{}:_-]+/u;

export type TfcrmParityFields = {
  text?: unknown[];
  structured?: unknown[];
};

export type TfcrmParityMode = "empty" | "exact" | "fuzzy" | "none";

export type TfcrmParitySearchResult<T> = {
  items: T[];
  mode: TfcrmParityMode;
  candidateLimit: number;
  evaluatedCandidates: number;
};

function tokens(value: unknown): string[] {
  const normalized = normalizeSearchText(value);
  return normalized ? normalized.split(" ").filter(Boolean) : [];
}

function normalizedValues(values: unknown[] | undefined): string[] {
  return (values ?? [])
    .map(value => normalizeSearchText(value))
    .filter(Boolean);
}

function exactTokenMatch(
  token: string,
  fields: TfcrmParityFields,
): boolean {
  return [
    ...normalizedValues(fields.text),
    ...normalizedValues(fields.structured),
  ].some(value => value.includes(token));
}

function candidateWords(values: unknown[] | undefined): string[] {
  return normalizedValues(values)
    .flatMap(value => value.split(WORD_SPLIT_RE))
    .map(value => value.trim())
    .filter(Boolean);
}

function fuzzyDistanceLimit(token: string): number {
  if (token.length <= 2) return 0;
  if (token.length <= 7) return 1;
  return 2;
}

function fuzzyThreshold(token: string): number {
  return token.length <= 4 ? 0.75 : 0.72;
}

export function tfcrmParityDamerauDistance(leftValue: unknown, rightValue: unknown): number {
  const left = Array.from(normalizeSearchText(leftValue));
  const right = Array.from(normalizeSearchText(rightValue));
  if (left.join("") === right.join("")) return 0;
  if (!left.length) return right.length;
  if (!right.length) return left.length;

  const rows = left.length + 1;
  const cols = right.length + 1;
  const matrix: number[][] = Array.from({ length: rows }, () => Array(cols).fill(0));
  for (let i = 0; i < rows; i += 1) matrix[i][0] = i;
  for (let j = 0; j < cols; j += 1) matrix[0][j] = j;

  for (let i = 1; i < rows; i += 1) {
    for (let j = 1; j < cols; j += 1) {
      const cost = left[i - 1] === right[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost,
      );
      if (
        i > 1 &&
        j > 1 &&
        left[i - 1] === right[j - 2] &&
        left[i - 2] === right[j - 1]
      ) {
        matrix[i][j] = Math.min(matrix[i][j], matrix[i - 2][j - 2] + 1);
      }
    }
  }

  return matrix[left.length][right.length];
}

export function isTfcrmParityFuzzyEligible(value: unknown): boolean {
  const query = normalizeSearchText(value);
  return query.length >= 3 && LETTER_RE.test(query) && !query.includes("@");
}

function fuzzyTokenMatch(token: string, fields: TfcrmParityFields): boolean {
  if (!LETTER_RE.test(token)) return false;
  const maxDistance = fuzzyDistanceLimit(token);
  if (maxDistance <= 0) return false;

  for (const word of candidateWords(fields.text)) {
    if (Math.abs(word.length - token.length) > maxDistance) continue;
    const distance = tfcrmParityDamerauDistance(token, word);
    if (distance > maxDistance) continue;
    const similarity = 1 - distance / Math.max(token.length, word.length, 1);
    if (similarity >= fuzzyThreshold(token)) return true;
  }
  return false;
}

export function matchesTfcrmParityExact(
  query: unknown,
  fields: TfcrmParityFields,
): boolean {
  const queryTokens = tokens(query);
  if (!queryTokens.length) return true;
  return queryTokens.every(token => exactTokenMatch(token, fields));
}

export function matchesTfcrmParityFuzzyFallback(
  query: unknown,
  fields: TfcrmParityFields,
): boolean {
  const queryTokens = tokens(query);
  if (!queryTokens.length) return true;
  return queryTokens.every(
    token => exactTokenMatch(token, fields) || fuzzyTokenMatch(token, fields),
  );
}

export function filterTfcrmParityExactFirst<T>(
  query: unknown,
  items: readonly T[],
  getFields: (item: T) => TfcrmParityFields,
  options: { candidateLimit?: number } = {},
): TfcrmParitySearchResult<T> {
  const normalized = normalizeSearchText(query);
  const candidateLimit = Math.max(
    1,
    Math.floor(options.candidateLimit ?? TFCRM_PARITY_LIST_CANDIDATE_LIMIT),
  );

  if (!normalized) {
    return {
      items: [...items],
      mode: "empty",
      candidateLimit,
      evaluatedCandidates: 0,
    };
  }

  const exact = items.filter(item => matchesTfcrmParityExact(normalized, getFields(item)));
  if (exact.length > 0) {
    return {
      items: exact,
      mode: "exact",
      candidateLimit,
      evaluatedCandidates: items.length,
    };
  }

  if (!isTfcrmParityFuzzyEligible(normalized)) {
    return {
      items: [],
      mode: "none",
      candidateLimit,
      evaluatedCandidates: 0,
    };
  }

  const candidates = items.slice(0, candidateLimit);
  const fuzzy = candidates.filter(item =>
    matchesTfcrmParityFuzzyFallback(normalized, getFields(item)),
  );

  return {
    items: fuzzy,
    mode: fuzzy.length ? "fuzzy" : "none",
    candidateLimit,
    evaluatedCandidates: candidates.length,
  };
}

export function buildTfcrmParitySuggestions<T>(
  query: unknown,
  items: readonly T[],
  getFields: (item: T) => TfcrmParityFields,
  options: {
    candidateLimit?: number;
    limit?: number;
  } = {},
): T[] {
  if (normalizeSearchText(query).length < TFCRM_PARITY_SUGGESTION_MIN_LENGTH) return [];

  const result = filterTfcrmParityExactFirst(query, items, getFields, {
    candidateLimit: options.candidateLimit,
  });

  return result.items.slice(
    0,
    Math.max(1, Math.floor(options.limit ?? TFCRM_PARITY_SUGGESTION_LIMIT)),
  );
}
'''

parity_test = r'''import { describe, expect, it } from "vitest";
import {
  TFCRM_PARITY_GLOBAL_CANDIDATE_LIMIT,
  TFCRM_PARITY_LIST_CANDIDATE_LIMIT,
  buildTfcrmParitySuggestions,
  filterTfcrmParityExactFirst,
  matchesTfcrmParityFuzzyFallback,
  tfcrmParityDamerauDistance,
} from "./systemSmartSearchParity";

describe("TFCRM-parity exact-first Smart Search", () => {
  const fields = (item: any) => ({
    text: [item.name, item.company],
    structured: [item.email, item.phone, item.id],
  });

  it("keeps TCRM stronger Arabic normalization", () => {
    const result = filterTfcrmParityExactFirst(
      "الامل",
      [{ name: "الأمل", id: 1 }],
      fields,
    );
    expect(result.mode).toBe("exact");
    expect(result.items).toHaveLength(1);
  });

  it("does not admit fuzzy rows while normalized exact rows exist", () => {
    const result = filterTfcrmParityExactFirst(
      "ahmed",
      [
        { id: 1, name: "Ahmed Furniture" },
        { id: 2, name: "Ahmd Furniture" },
      ],
      fields,
    );
    expect(result.mode).toBe("exact");
    expect(result.items.map(item => item.id)).toEqual([1]);
  });

  it("uses fuzzy only when the exact stage returns zero", () => {
    const result = filterTfcrmParityExactFirst(
      "mohmaed",
      [{ id: 1, name: "Mohamed Furniture" }],
      fields,
    );
    expect(result.mode).toBe("fuzzy");
    expect(result.items.map(item => item.id)).toEqual([1]);
  });

  it("supports adjacent transposition", () => {
    expect(tfcrmParityDamerauDistance("mohmaed", "mohamed")).toBe(1);
  });

  it("never fuzzes structured email/phone/id values", () => {
    expect(
      matchesTfcrmParityFuzzyFallback("ahmd@example.com", {
        structured: ["ahmed@example.com"],
      }),
    ).toBe(false);
    expect(
      matchesTfcrmParityFuzzyFallback("1235", {
        structured: ["1234"],
      }),
    ).toBe(false);
  });

  it("caps fuzzy candidates after the authorized collection is supplied", () => {
    const items = Array.from({ length: 1200 }, (_, index) => ({
      id: index + 1,
      name: index === 1100 ? "Mohamed Furniture" : `row-${index}`,
    }));
    const result = filterTfcrmParityExactFirst("mohmaed", items, fields);
    expect(result.candidateLimit).toBe(TFCRM_PARITY_LIST_CANDIDATE_LIMIT);
    expect(result.evaluatedCandidates).toBe(TFCRM_PARITY_LIST_CANDIDATE_LIMIT);
    expect(result.items).toHaveLength(0);
  });

  it("exposes the TFCRM-style global candidate cap", () => {
    expect(TFCRM_PARITY_GLOBAL_CANDIDATE_LIMIT).toBe(500);
    expect(TFCRM_PARITY_LIST_CANDIDATE_LIMIT).toBe(1000);
  });

  it("suggestions start after two normalized characters and cap at six", () => {
    const items = Array.from({ length: 10 }, (_, index) => ({
      id: index + 1,
      name: `Ahmed ${index}`,
    }));
    expect(buildTfcrmParitySuggestions("a", items, fields)).toEqual([]);
    expect(buildTfcrmParitySuggestions("ah", items, fields)).toHaveLength(6);
  });
});
'''

server_ts = r'''import {
  TFCRM_PARITY_LIST_CANDIDATE_LIMIT,
  isTfcrmParityFuzzyEligible,
  type TfcrmParityMode,
} from "@shared/systemSmartSearchParity";

export type ExactFirstServerSearchResult<T> = {
  value: T;
  mode: Extract<TfcrmParityMode, "exact" | "fuzzy" | "none">;
  candidateLimit: number;
};

export async function runExactFirstServerSearch<T>(options: {
  query: unknown;
  runExact: () => Promise<T>;
  runFuzzy: (candidateLimit: number) => Promise<T>;
  hasMatches: (value: T) => boolean;
  candidateLimit?: number;
}): Promise<ExactFirstServerSearchResult<T>> {
  const candidateLimit = Math.max(
    1,
    Math.floor(options.candidateLimit ?? TFCRM_PARITY_LIST_CANDIDATE_LIMIT),
  );

  const exact = await options.runExact();
  if (options.hasMatches(exact)) {
    return { value: exact, mode: "exact", candidateLimit };
  }

  if (!isTfcrmParityFuzzyEligible(options.query)) {
    return { value: exact, mode: "none", candidateLimit };
  }

  const fuzzy = await options.runFuzzy(candidateLimit);
  return {
    value: fuzzy,
    mode: options.hasMatches(fuzzy) ? "fuzzy" : "none",
    candidateLimit,
  };
}
'''

server_test = r'''import { describe, expect, it, vi } from "vitest";
import { runExactFirstServerSearch } from "./searchExactFirstFallback";

describe("runExactFirstServerSearch", () => {
  it("does not execute fuzzy when exact has matches", async () => {
    const fuzzy = vi.fn(async () => ["fuzzy"]);
    const result = await runExactFirstServerSearch({
      query: "ahmed",
      runExact: async () => ["exact"],
      runFuzzy: fuzzy,
      hasMatches: rows => rows.length > 0,
    });
    expect(result.mode).toBe("exact");
    expect(fuzzy).not.toHaveBeenCalled();
  });

  it("executes fuzzy only after exact returns zero", async () => {
    const result = await runExactFirstServerSearch({
      query: "mohmaed",
      runExact: async () => [],
      runFuzzy: async limit => (limit === 1000 ? ["Mohamed"] : []),
      hasMatches: rows => rows.length > 0,
    });
    expect(result.mode).toBe("fuzzy");
    expect(result.value).toEqual(["Mohamed"]);
  });

  it("does not fuzzy numeric-only queries", async () => {
    const fuzzy = vi.fn(async () => ["bad"]);
    const result = await runExactFirstServerSearch({
      query: "12345",
      runExact: async () => [],
      runFuzzy: fuzzy,
      hasMatches: rows => rows.length > 0,
    });
    expect(result.mode).toBe("none");
    expect(fuzzy).not.toHaveBeenCalled();
  });
});
'''

audit_ts = r'''import fs from "node:fs";
import path from "node:path";

const strict = process.argv.includes("--strict");
const clientRoot = path.resolve(process.cwd(), "client/src");
const serverRoots = [
  path.resolve(process.cwd(), "server/routes"),
  path.resolve(process.cwd(), "server/services"),
  path.resolve(process.cwd(), "server/db.ts"),
];

const candidatePatterns = [
  /placeholder\s*=\s*(?:\{[^\n]*(?:search|Search|بحث|ابحث)[^\n]*\}|["'`][^"'`]*(?:search|Search|بحث|ابحث)[^"'`]*["'`])/,
  /placeholder\s*=\s*\{[^}]*\bt\(\s*["'](?:search|bdSearch|bdSearchCompanies)["']/,
  /type\s*=\s*["']search["']/,
  /<CommandInput\b/,
];

const phase6Exempt = /SMART_SEARCH_AUDIT_EXEMPT:\s*(.+)/;
const parityIntegrated = /TFCRM_SEARCH_PARITY_INTEGRATED:\s*(.+)/;
const parityExempt = /TFCRM_SEARCH_PARITY_EXEMPT:\s*(.+)/;
const serverParity = /TFCRM_SEARCH_PARITY_SERVER:\s*(.+)/;
const WINDOW = 18;

function walk(target: string): string[] {
  if (!fs.existsSync(target)) return [];
  const stat = fs.statSync(target);
  if (stat.isFile()) return [target];
  return fs.readdirSync(target, { withFileTypes: true }).flatMap(entry => {
    const full = path.join(target, entry.name);
    if (entry.isDirectory()) return walk(full);
    return /\.(ts|tsx)$/.test(entry.name) ? [full] : [];
  });
}

function markerNear(lines: string[], lineIndex: number) {
  const from = Math.max(0, lineIndex - WINDOW);
  const to = Math.min(lines.length, lineIndex + WINDOW + 1);
  for (let index = from; index < to; index += 1) {
    const line = lines[index];
    const phase6 = line.match(phase6Exempt);
    if (phase6) return { status: "exempt" as const, reason: phase6[1].trim() };
    const exempt = line.match(parityExempt);
    if (exempt) return { status: "exempt" as const, reason: exempt[1].trim() };
    const integrated = line.match(parityIntegrated);
    if (integrated) return { status: "integrated" as const, reason: integrated[1].trim() };
  }
  return null;
}

const uiRows: Array<{
  file: string;
  line: number;
  status: "integrated" | "exempt" | "pending";
  reason: string;
}> = [];

for (const file of walk(clientRoot)) {
  const source = fs.readFileSync(file, "utf8");
  const lines = source.split(/\r?\n/);
  lines.forEach((line, index) => {
    if (!candidatePatterns.some(pattern => pattern.test(line))) return;
    const marker = markerNear(lines, index);
    uiRows.push({
      file: path.relative(process.cwd(), file).replace(/\\/g, "/"),
      line: index + 1,
      status: marker?.status ?? "pending",
      reason: marker?.reason ?? "",
    });
  });
}

const serverRows: Array<{
  file: string;
  line: number;
  status: "integrated" | "pending";
  reason: string;
}> = [];

for (const root of serverRoots) {
  for (const file of walk(root)) {
    if (file.endsWith("searchNormalizationSql.ts")) continue;
    const source = fs.readFileSync(file, "utf8");
    if (!source.includes("fuzzyContains(")) continue;
    const lines = source.split(/\r?\n/);
    lines.forEach((line, index) => {
      if (!line.includes("fuzzyContains(")) return;
      const from = Math.max(0, index - WINDOW);
      const to = Math.min(lines.length, index + WINDOW + 1);
      let reason = "";
      for (let markerIndex = from; markerIndex < to; markerIndex += 1) {
        const match = lines[markerIndex].match(serverParity);
        if (match) {
          reason = match[1].trim();
          break;
        }
      }
      serverRows.push({
        file: path.relative(process.cwd(), file).replace(/\\/g, "/"),
        line: index + 1,
        status: reason ? "integrated" : "pending",
        reason,
      });
    });
  }
}

const uiPending = uiRows.filter(row => row.status === "pending");
const serverPending = serverRows.filter(row => row.status === "pending");

console.log("# TCRM TFCRM-Parity Smart Search Audit");
console.log("");
console.log(
  `UI Candidates: ${uiRows.length} | Integrated: ${uiRows.filter(r => r.status === "integrated").length} | Exempt: ${uiRows.filter(r => r.status === "exempt").length} | Pending: ${uiPending.length}`,
);
console.log(
  `Server fuzzy callsites: ${serverRows.length} | Reviewed: ${serverRows.filter(r => r.status === "integrated").length} | Pending: ${serverPending.length}`,
);

if (uiPending.length) {
  console.log("\n## Pending UI controls");
  for (const row of uiPending) console.log(`- ${row.file}:${row.line}`);
}
if (serverPending.length) {
  console.log("\n## Pending server fuzzy callsites");
  for (const row of serverPending) console.log(`- ${row.file}:${row.line}`);
}

if (strict && (uiPending.length || serverPending.length)) {
  console.error(
    `\nTFCRM parity audit failed: UI pending=${uiPending.length}, server pending=${serverPending.length}.`,
  );
  process.exitCode = 1;
}
'''

files = {
    "shared/systemSmartSearchParity.ts": parity_ts,
    "shared/systemSmartSearchParity.test.ts": parity_test,
    "server/utils/searchExactFirstFallback.ts": server_ts,
    "server/utils/searchExactFirstFallback.test.ts": server_test,
    "scripts/audit-tfcrm-search-parity.ts": audit_ts,
}

# Preflight every target before writing anything, so failure is atomic.
for rel in files:
    dest = root / rel
    if dest.exists():
        raise SystemExit(f"Refusing to overwrite existing parity artifact: {rel}")

smart = root / "client/src/components/search/SmartSearchBar.tsx"
source = smart.read_text(encoding="utf-8")

if 'from "@shared/searchNormalization"' not in source:
    import_anchor = 'import VoiceSearchButton from "./VoiceSearchButton";'
    if import_anchor not in source:
        raise SystemExit("SmartSearchBar import anchor changed; adapt manually.")
else:
    import_anchor = None

if "const suggestionsReady =" not in source:
    language_anchor = '  const isRTL = language.startsWith("ar");'
    if language_anchor not in source:
        raise SystemExit("SmartSearchBar language anchor changed; adapt manually.")
else:
    language_anchor = None

new_source = source
if import_anchor:
    new_source = new_source.replace(
        import_anchor,
        import_anchor + '\nimport { normalizeSearchText } from "@shared/searchNormalization";',
        1,
    )

new_source = new_source.replace(".slice(0, 8);", ".slice(0, 6);")
if language_anchor:
    new_source = new_source.replace(
        language_anchor,
        language_anchor + '\n  const suggestionsReady = normalizeSearchText(value).length >= 2;',
        1,
    )

new_source = new_source.replace(
    'list={uniqueSuggestions.length ? datalistId : undefined}',
    'list={suggestionsReady && uniqueSuggestions.length ? datalistId : undefined}',
)
new_source = new_source.replace(
    '{uniqueSuggestions.length > 0 && (',
    '{suggestionsReady && uniqueSuggestions.length > 0 && (',
)

if "suggestionsReady" not in new_source or ".slice(0, 6);" not in new_source:
    raise SystemExit("SmartSearchBar suggestion policy preflight failed; adapt manually.")

# All checks passed: now write the patch artifacts and UI policy change.
for rel, content in files.items():
    dest = root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
smart.write_text(new_source, encoding="utf-8")

print("TFCRM parity bootstrap applied.")
print("Added:")
for rel in files:
    print(f"- {rel}")
print("- updated client/src/components/search/SmartSearchBar.tsx (suggestions min=2, max=6)")
print("")
print("IMPORTANT: application is not complete until every true Phase 6 search control is migrated")
print("to exact-first/fuzzy-fallback behavior and parity strict audit reaches zero pending.")
