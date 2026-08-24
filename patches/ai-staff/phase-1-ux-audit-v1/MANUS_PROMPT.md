# Manus Prompt — TCRM AI Staff Phase 1 UX/UI Audit

Perform TCRM AI STAFF PHASE 1 UX/UI AUDIT — SCREENSHOT + STRUCTURE REVIEW ONLY.

LIVE PROJECT:
`/var/www/TCRM-MAIN`

PRODUCTION:
`https://sales.tamiyouzplaform.com`

EXPECTED BRANCH:
`main`

EXPECTED HEAD:
`0d5696b0946142c1836cefd601c597db5a3f4187`

REFERENCE SPEC:
`mohamedamouseo-a11y/TCRM-main-patchs-/patches/ai-staff/phase-1-ux-audit-v1/README.md`

IMPORTANT:
- READ ONLY.
- DO NOT modify application source.
- DO NOT redesign anything yet.
- DO NOT modify backend, API, DB, migrations, permissions, or environment.
- DO NOT touch `external/mautic`.
- DO NOT trigger customer/business actions.
- DO NOT create a branch.
- DO NOT manually commit or push.
- Phase 1 has no application patch to push to TCRM-MAIN. The purpose is to produce the visual baseline that ChatGPT will use to author Phase 2. Confirm remote `main` remains unchanged at the end.

STEP 1 — PREFLIGHT

From `/var/www/TCRM-MAIN` run:

`git branch --show-current`
`git rev-parse HEAD`
`git status --short`

Required:
- branch = `main`
- HEAD = `0d5696b0946142c1836cefd601c597db5a3f4187`
- application worktree clean

If HEAD differs, STOP and report the exact new HEAD so ChatGPT can rebase the phase reference before continuing.

STEP 2 — AUTHENTICATED SCREENSHOT AUDIT

Open production in an authenticated desktop browser and audit these routes:

1. `/darwish`
2. `/zaghloul`
3. `/tara`
4. `/felfel`

For EACH route capture:
- hero / identity area
- KPI row
- main navigation/tabs
- each major content section by scrolling
- enough sequential screenshots to reconstruct the full page from top to bottom

Do not click any button that creates, sends, approves, executes, joins, changes settings, or mutates business data.

You MAY switch between existing non-mutating tabs only to inspect layout/content.

STEP 3 — DARWISH DEEP STRUCTURE AUDIT

Darwish is the priority.

Record the exact visible section order from top to bottom.
Estimate page length in desktop viewport screenfuls.

Identify:
- duplicated KPI/status information
- repeated intelligence summaries
- sections that compete for equal visual priority
- sections that should become top-level tabs
- sections that can become grouped secondary tabs / accordions
- sections that should remain immediately visible
- areas causing excessive scrolling
- heading/card hierarchy inconsistencies
- opportunities to create a concise supervisor workspace without removing any capability

Do NOT propose removing features.

STEP 4 — OTHER AGENT CONSISTENCY AUDIT

For Zaghloul, Tara and Felfel compare:
- hero proportions
- portrait treatment
- title/status hierarchy
- skills presentation
- KPI card dimensions and density
- tab/nav treatment
- page width and spacing
- lower-section organization
- empty/loading states
- bilingual/RTL presentation

Identify what should become the shared AI Staff design standard and what should remain agent-specific.

STEP 5 — SOURCE MAPPING — READ ONLY

Identify exact source page/components powering the visible structures.

For each agent report:
- route
- page file
- major child components
- existing tab/navigation implementation
- current live query/data sources used for top KPIs

Do not edit files.

STEP 6 — REPORT PACKAGE

Create a report package containing:

`TCRM-AI-Staff-Phase-1-UX-Audit-Report.md`

and all available screenshot evidence.

The report must contain:

`BASE_HEAD=`
`FINAL_HEAD=`
`GITHUB_MAIN_UNCHANGED=YES/NO`

`DARWISH_SCREENFULS=`
`DARWISH_SECTION_ORDER=`
`DARWISH_DUPLICATION_FINDINGS=`
`DARWISH_RECOMMENDED_INFORMATION_ARCHITECTURE=`

`ZAGHLOUL_FINDINGS=`
`TARA_FINDINGS=`
`FELFEL_FINDINGS=`

`SHARED_AI_STAFF_DESIGN_RULES=`
`AGENT_SPECIFIC_EXCEPTIONS=`

`CODE_CHANGED=NO`
`COMMIT=NO`
`PUSH=NO`
`DATABASE_CHANGED=NO`
`MIGRATIONS_RUN=NO`
`MAUTIC_FILES_TOUCHED=0`

Attach the report and screenshot package back to the user.
