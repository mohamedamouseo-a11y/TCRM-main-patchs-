# TCRM Help Center — Phase 1: UX / Navigation / SEO Foundation

## Target
- Source repo: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Expected base commit: `c3607f2013b470863cee31750e9ce1c4a8b6ba2e`
- Target file only: `client/src/pages/HelpCenter.tsx`

## Goal
Upgrade the existing premium TCRM Help Center without replacing its current content or visual identity. This phase establishes professional URL/navigation behavior, article-level SEO, and a reusable video-guide slot before later Rakan/CMS/content-coverage phases.

## What Phase 1 changes
1. **Localized permanent URLs**
   - Help Center: `/:lang/help-center`
   - Category: `/:lang/help-center/:category`
   - Section: `/:lang/help-center/:category--:section`
   - Article: `/:lang/help-center/:category--:section--:article`
2. **No more timeout-based article opening**
   - Search and Popular Article clicks navigate directly to the article URL.
   - Opening/collapsing an article keeps the URL synchronized.
   - Refreshing a direct article URL reopens the correct article.
3. **Professional breadcrumbs**
   - Category → Section → Article.
   - Locale is preserved in every Help Center navigation action.
4. **Article utility bar**
   - Copy permanent article link.
   - Open article in a new tab.
   - Detect and label step-by-step articles.
   - Optional `videoUrl`, `videoTitleEn`, and `videoTitleAr` fields; a video button appears automatically only when a real URL is supplied.
5. **Article/section/category SEO foundation**
   - Dynamic title and meta description.
   - Canonical URL.
   - `index, follow` robots metadata.
   - Open Graph + Twitter metadata through the existing `applyDocumentSeo` helper.
   - Per-article keywords.
   - `TechArticle` JSON-LD for direct articles and `CollectionPage` JSON-LD for browsing pages.

## Explicitly not in Phase 1
- No article content is deleted or rewritten.
- No permissions, CRM workflows, database schema, or API behavior changes.
- No fake video links are inserted.
- Rakan is **not guessed or hard-wired** in this phase. Its exact frontend contract will be inspected and integrated contextually in Phase 2.
- No CMS/database migration yet.

## Apply
Run from the **TCRM source repo root**:

```bash
python3 /path/to/TCRM-main-patchs-/TCRM-HELP-CENTER-PHASE-1-UX-NAV-SEO-V1/APPLY_PATCH.py
pnpm check
pnpm build
```

The script is deterministic and aborts if the source HEAD is not the expected base commit or if `HelpCenter.tsx` has local changes.

## Server / push workflow
1. OpenHands applies this patch on the server and runs only the requested verification.
2. Review the result in the deployed TCRM Help Center.
3. Push the server source to TCRM `main` from the system when approved.
4. Next phase starts only after reading the newest TCRM `main` commit produced by that push.

## Planned continuation
- **Phase 2:** Rakan contextual Help Assistant + article-aware prompts/sources.
- **Phase 3:** full-system feature coverage audit, missing articles, professional step templates, screenshots/video URLs.
- **Phase 4:** Help Center CMS, drafts/publishing/versioning/feedback/analytics.
- **Phase 5:** search relevance, SEO/content QA, responsive/accessibility/performance hardening.
