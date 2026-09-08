# TCRM Help Center Upgrade Roadmap

## Working rule
Every phase is incremental and starts from the **latest pushed TCRM `main` commit**. The implementation lives as a deterministic bundle in `TCRM-main-patchs-`; OpenHands only applies the bundle and runs the requested checks on the server. The server/system push is performed separately, then the next phase is rebased conceptually on that new `main` state.

This keeps OpenHands usage low: no repository exploration, no autonomous redesign, no broad refactoring.

## Phase 1 — UX / Navigation / SEO Foundation
Status: **PATCH READY**

- Premium Help Center UX polish without replacing current TCRM identity/content.
- Permanent localized category/section/article links.
- URL-driven article opening and professional breadcrumbs.
- Article copy/open utilities.
- Optional explainer-video link slot.
- Dynamic article/category/section SEO and structured data.

Patch: `TCRM-HELP-CENTER-PHASE-1-UX-NAV-SEO-V1/`

## Phase 2 — Rakan Contextual Help
Status: Planned after Phase 1 server push.

- Inspect the exact current Rakan frontend contract from the newest TCRM main.
- Add contextual “Ask Rakan” entry points from Help Center articles.
- Pass current category/section/article context safely.
- Allow Rakan answers to point users back to relevant Help Center sources/deep links.
- No duplicate AI widget if an existing Rakan surface can be reused.

## Phase 3 — Full-System Documentation Coverage
Status: Planned.

- Inventory every visible TCRM module, page, role-specific area, integration, settings surface, and important feature from the current application routes/code.
- Map every feature to a Help Center category → section → article.
- Produce a gap report for missing/outdated documentation.
- Add missing articles in Arabic and English.
- Standardize articles into professional task-oriented structures where appropriate: purpose, prerequisites, steps, expected result, troubleshooting, permissions/role notes, related links.
- Add real screenshots and real explainer-video URLs where provided; never fabricate URLs.
- Add “Related articles / Next step” navigation.

## Phase 4 — Help Center Management Platform
Status: Planned.

- Admin/Super Admin Help Center CMS.
- Draft/published status, pinning, categories/tags, versions, EN/AR content.
- Video URL and supporting media management.
- Helpful/not-helpful feedback and optional comment.
- Views/search/query analytics and content-gap signals.
- “What’s New” / product update articles.

## Phase 5 — Quality / Discoverability / Hardening
Status: Planned.

- Search relevance and zero-result improvements.
- SEO content QA: titles, descriptions, headings, internal links, duplicate/canonical checks, structured data.
- Responsive/mobile UX QA, RTL/LTR consistency, accessibility/keyboard behavior.
- Performance and bundle impact review.
- Broken/dead Help links audit.
- Final coverage report proving which TCRM features are documented and identifying any remaining gaps.

## Low-credit OpenHands contract
For every phase, OpenHands receives only:
1. deterministic patch path,
2. exact apply command,
3. exact check/build command,
4. instruction to stop on mismatch/error and not improvise.

OpenHands must not commit or push. The next phase begins only after the server result is pushed to TCRM `main` and that new commit is read.
