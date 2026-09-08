#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

EXPECTED_BASE = "c3607f2013b470863cee31750e9ce1c4a8b6ba2e"
MARKER = "TCRM_HELP_CENTER_PHASE_1_UX_NAV_SEO_V1"
TARGET = Path("client/src/pages/HelpCenter.tsx")


def fail(message: str) -> None:
    print(f"[HELP-CENTER-P1] ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        fail(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected exactly 1 match, found {count}. Source is not the expected base.")
    return text.replace(old, new, 1)


if not TARGET.exists():
    fail(f"Run this script from the TCRM repository root. Missing: {TARGET}")

head = git("rev-parse", "HEAD")
if head != EXPECTED_BASE:
    fail(f"Expected TCRM main base {EXPECTED_BASE}, found {head}. Pull/push workflow state must be reconciled first.")

if git("status", "--porcelain", "--", str(TARGET)):
    fail(f"{TARGET} has local changes. Refusing to overwrite them.")

original = TARGET.read_text(encoding="utf-8")
if MARKER in original:
    print("[HELP-CENTER-P1] Patch already applied; nothing to do.")
    raise SystemExit(0)

text = original

text = replace_once(
    text,
    'import { useThemeTokens } from "@/contexts/ThemeTokenContext";\n',
    'import { useThemeTokens } from "@/contexts/ThemeTokenContext";\nimport { applyDocumentSeo } from "@/lib/seo";\n',
    "seo import",
)

text = replace_once(
    text,
    '  Sparkles, UserRound, Users, X, BookOpen, Mail, Phone,\n  CreditCard\n',
    '  Sparkles, UserRound, Users, X, BookOpen, Mail, Phone, Copy,\n  ExternalLink, PlayCircle, CreditCard\n',
    "help action icons",
)

text = replace_once(
    text,
    'const getIcon = (name: string) => ICON[name] || <HelpCircle className="h-5 w-5" />;\n\n\ninterface Article {\n',
    '''const getIcon = (name: string) => ICON[name] || <HelpCircle className="h-5 w-5" />;\n\n// TCRM_HELP_CENTER_PHASE_1_UX_NAV_SEO_V1\ntype HelpLanguage = "en" | "ar";\n\nfunction helpBasePath(lang: HelpLanguage): string {\n  return `/${lang}/help-center`;\n}\n\nfunction helpCategoryPath(lang: HelpLanguage, categoryId: string): string {\n  return `${helpBasePath(lang)}/${categoryId}`;\n}\n\nfunction helpSectionPath(lang: HelpLanguage, categoryId: string, sectionId: string): string {\n  return `${helpBasePath(lang)}/${categoryId}--${sectionId}`;\n}\n\nfunction helpArticlePath(lang: HelpLanguage, categoryId: string, sectionId: string, articleId: string): string {\n  return `${helpBasePath(lang)}/${categoryId}--${sectionId}--${articleId}`;\n}\n\nfunction stripHelpHtml(value: string): string {\n  return value\n    .replace(/<script[\\s\\S]*?<\\/script>/gi, " ")\n    .replace(/<style[\\s\\S]*?<\\/style>/gi, " ")\n    .replace(/<[^>]+>/g, " ")\n    .replace(/&nbsp;/gi, " ")\n    .replace(/&amp;/gi, "&")\n    .replace(/&quot;/gi, '\"')\n    .replace(/&#39;/gi, "'")\n    .replace(/\\s+/g, " ")\n    .trim();\n}\n\n\ninterface Article {\n''',
    "help path and seo helpers",
)

text = replace_once(
    text,
    '  keywords: string[];\n  popular?: boolean;\n}',
    '  keywords: string[];\n  popular?: boolean;\n  videoUrl?: string;\n  videoTitleEn?: string;\n  videoTitleAr?: string;\n}',
    "article video fields",
)

text = replace_once(
    text,
    '''  const [searchQuery, setSearchQuery] = useState("");\n  const [activeCategoryId, setActiveCategoryId] = useState(categories[0]?.id || "");\n  const [expandedArticle, setExpandedArticle] = useState<string | null>(null);\n  const searchInputRef = useRef<HTMLInputElement>(null);\n\n  // Parse slug: "catId--secId" or "catId"\n  const slug = params?.slug || null;\n  const urlCatId = slug ? slug.split("--")[0] : null;\n  const urlSecId = slug && slug.includes("--") ? slug.split("--")[1] : null;\n''',
    '''  const [searchQuery, setSearchQuery] = useState("");\n  const [activeCategoryId, setActiveCategoryId] = useState(categories[0]?.id || "");\n  const [expandedArticle, setExpandedArticle] = useState<string | null>(null);\n  const [copiedArticleId, setCopiedArticleId] = useState<string | null>(null);\n  const searchInputRef = useRef<HTMLInputElement>(null);\n\n  // Professional deep-link structure:\n  // /:lang/help-center/:category\n  // /:lang/help-center/:category--:section\n  // /:lang/help-center/:category--:section--:article\n  const slug = params?.slug || null;\n  const slugParts = slug ? slug.split("--") : [];\n  const urlCatId = slugParts[0] || null;\n  const urlSecId = slugParts[1] || null;\n  const urlArticleId = slugParts[2] || null;\n''',
    "deep link parser",
)

text = replace_once(
    text,
    '''  const activeSection = useMemo(\n    () => (urlSecId ? activeCategory?.sections.find((s) => s.id === urlSecId) : null),\n    [urlSecId, activeCategory]\n  );\n\n  const searchResults = useMemo(() => {\n''',
    '''  const activeSection = useMemo(\n    () => (urlSecId ? activeCategory?.sections.find((s) => s.id === urlSecId) : null),\n    [urlSecId, activeCategory]\n  );\n\n  const activeArticle = useMemo(\n    () => (urlArticleId ? activeSection?.articles.find((article) => article.id === urlArticleId) || null : null),\n    [urlArticleId, activeSection]\n  );\n\n  useEffect(() => {\n    if (urlArticleId && activeArticle) {\n      setExpandedArticle(urlArticleId);\n      return;\n    }\n    if (!urlArticleId) {\n      setExpandedArticle(null);\n    }\n  }, [urlArticleId, activeArticle]);\n\n  useEffect(() => {\n    const categoryName = activeCategory ? (isEn ? activeCategory.nameEn : activeCategory.nameAr) : "Tamiyouz CRM";\n    const sectionName = activeSection ? (isEn ? activeSection.nameEn : activeSection.nameAr) : "";\n    const articleTitle = activeArticle ? (isEn ? activeArticle.questionEn : activeArticle.questionAr) : "";\n    const articleAnswer = activeArticle ? (isEn ? activeArticle.answerEn : activeArticle.answerAr) : "";\n\n    const pageTitle = articleTitle || sectionName || (urlCatId ? categoryName : (isEn ? "Help Center" : "مركز المساعدة"));\n    const fallbackDescription = isEn\n      ? "Guides, tutorials, troubleshooting, and step-by-step help for every Tamiyouz CRM feature."\n      : "أدلة وشروحات وحلول للمشكلات وخطوات واضحة لكل ميزة في نظام Tamiyouz CRM.";\n    const sourceDescription = articleAnswer || (activeSection ? (isEn ? activeSection.descriptionEn : activeSection.descriptionAr) : activeCategory ? (isEn ? activeCategory.descriptionEn : activeCategory.descriptionAr) : fallbackDescription);\n    const description = (stripHelpHtml(sourceDescription) || fallbackDescription).slice(0, 158);\n\n    const canonicalPath = activeArticle && activeSection && activeCategory\n      ? helpArticlePath(lang, activeCategory.id, activeSection.id, activeArticle.id)\n      : activeSection && activeCategory\n        ? helpSectionPath(lang, activeCategory.id, activeSection.id)\n        : urlCatId && activeCategory\n          ? helpCategoryPath(lang, activeCategory.id)\n          : helpBasePath(lang);\n\n    const keywords = Array.from(new Set([\n      "Tamiyouz CRM",\n      "TCRM",\n      categoryName,\n      sectionName,\n      ...(activeArticle?.keywords || []),\n    ].filter(Boolean)));\n\n    const absoluteUrl = new URL(canonicalPath, window.location.origin).toString();\n    applyDocumentSeo({\n      title: `${pageTitle} | Tamiyouz CRM Help Center`,\n      description,\n      keywords,\n      canonicalPath,\n      robots: "index, follow",\n      ogType: activeArticle ? "article" : "website",\n      lang,\n      jsonLd: activeArticle\n        ? {\n            "@context": "https://schema.org",\n            "@type": "TechArticle",\n            headline: articleTitle,\n            description,\n            inLanguage: lang,\n            url: absoluteUrl,\n            isPartOf: {\n              "@type": "WebSite",\n              name: "Tamiyouz CRM Help Center",\n              url: new URL(helpBasePath(lang), window.location.origin).toString(),\n            },\n          }\n        : {\n            "@context": "https://schema.org",\n            "@type": "CollectionPage",\n            name: pageTitle,\n            description,\n            inLanguage: lang,\n            url: absoluteUrl,\n          },\n    });\n  }, [lang, isEn, urlCatId, activeCategory, activeSection, activeArticle]);\n\n  const searchResults = useMemo(() => {\n''',
    "article state and dynamic seo",
)

text = replace_once(
    text,
    '''  const handleCategoryClick = useCallback((catId: string) => {\n    setActiveCategoryId(catId);\n    navigate("/help-center");\n  }, [navigate]);\n\n  const handleSectionClick = useCallback((catId: string, secId: string) => {\n    navigate(`/help-center/${catId}--${secId}`);\n  }, [navigate]);\n\n  const handleSearchResultClick = useCallback((result: SearchResult) => {\n    setSearchQuery("");\n    navigate(`/help-center/${result.categoryId}--${result.sectionId}`);\n    setTimeout(() => setExpandedArticle(result.id), 100);\n  }, [navigate]);\n''',
    '''  const handleCategoryClick = useCallback((catId: string) => {\n    setActiveCategoryId(catId);\n    setExpandedArticle(null);\n    navigate(helpCategoryPath(lang, catId));\n  }, [lang, navigate]);\n\n  const handleSectionClick = useCallback((catId: string, secId: string) => {\n    setExpandedArticle(null);\n    navigate(helpSectionPath(lang, catId, secId));\n  }, [lang, navigate]);\n\n  const handleSearchResultClick = useCallback((result: SearchResult) => {\n    setSearchQuery("");\n    setActiveCategoryId(result.categoryId);\n    setExpandedArticle(result.id);\n    navigate(helpArticlePath(lang, result.categoryId, result.sectionId, result.id));\n  }, [lang, navigate]);\n\n  const handleCopyArticleLink = useCallback(async (categoryId: string, sectionId: string, articleId: string) => {\n    const absoluteUrl = new URL(helpArticlePath(lang, categoryId, sectionId, articleId), window.location.origin).toString();\n    try {\n      await navigator.clipboard.writeText(absoluteUrl);\n    } catch {\n      const textarea = document.createElement("textarea");\n      textarea.value = absoluteUrl;\n      textarea.style.position = "fixed";\n      textarea.style.opacity = "0";\n      document.body.appendChild(textarea);\n      textarea.select();\n      document.execCommand("copy");\n      textarea.remove();\n    }\n    setCopiedArticleId(articleId);\n    window.setTimeout(() => {\n      setCopiedArticleId((current) => current === articleId ? null : current);\n    }, 1600);\n  }, [lang]);\n''',
    "localized navigation and copy link",
)

text = replace_once(
    text,
    '''                    <button onClick={() => navigate("/help-center")}\n                      className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors shadow-sm">\n                      {isRTL ? <ArrowRight className="h-4 w-4" /> : <ArrowLeft className="h-4 w-4" />}\n                      {isEn ? "Back" : "رجوع"}\n                    </button>\n                    <div className="flex items-center gap-1.5 text-xs text-slate-400">\n                      <span>{isEn ? activeCategory.nameEn : activeCategory.nameAr}</span>\n                      <span>›</span>\n                      <span className="text-slate-600 font-medium">{isEn ? activeSection.nameEn : activeSection.nameAr}</span>\n                    </div>\n''',
    '''                    <button onClick={() => navigate(helpCategoryPath(lang, activeCategory.id))}\n                      className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors shadow-sm">\n                      {isRTL ? <ArrowRight className="h-4 w-4" /> : <ArrowLeft className="h-4 w-4" />}\n                      {isEn ? "Back" : "رجوع"}\n                    </button>\n                    <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-400">\n                      <button\n                        type="button"\n                        onClick={() => navigate(helpCategoryPath(lang, activeCategory.id))}\n                        className="hover:text-slate-700 transition-colors"\n                      >\n                        {isEn ? activeCategory.nameEn : activeCategory.nameAr}\n                      </button>\n                      <span>›</span>\n                      <button\n                        type="button"\n                        onClick={() => navigate(helpSectionPath(lang, activeCategory.id, activeSection.id))}\n                        className={`${activeArticle ? "hover:text-slate-700" : "text-slate-600 font-medium"} transition-colors`}\n                      >\n                        {isEn ? activeSection.nameEn : activeSection.nameAr}\n                      </button>\n                      {activeArticle ? (\n                        <>\n                          <span>›</span>\n                          <span className="max-w-[360px] truncate text-slate-700 font-semibold">\n                            {isEn ? activeArticle.questionEn : activeArticle.questionAr}\n                          </span>\n                        </>\n                      ) : null}\n                    </div>\n''',
    "interactive breadcrumbs",
)

text = replace_once(
    text,
    '''                        <Accordion key={art.id} type="single" collapsible\n                          value={expandedArticle === art.id ? art.id : undefined}\n                          onValueChange={(v) => setExpandedArticle(v || null)}>\n''',
    '''                        <Accordion key={art.id} type="single" collapsible\n                          value={expandedArticle === art.id ? art.id : undefined}\n                          onValueChange={(v) => {\n                            setExpandedArticle(v || null);\n                            navigate(v\n                              ? helpArticlePath(lang, activeCategory.id, activeSection.id, v)\n                              : helpSectionPath(lang, activeCategory.id, activeSection.id));\n                          }}>\n''',
    "url-driven accordion",
)

text = replace_once(
    text,
    '''                            <AccordionContent className="px-5 pt-5 pb-6 ps-[4.25rem]">\n                              <div className="article-content max-w-none" dangerouslySetInnerHTML={{ __html: isEn ? art.answerEn : art.answerAr }} />\n                            </AccordionContent>\n''',
    '''                            <AccordionContent className="px-5 pt-5 pb-6 ps-[4.25rem]">\n                              <div\n                                className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border px-3 py-2.5"\n                                style={{ borderColor: `${activeCategory.color}22`, background: `${activeCategory.color}08` }}\n                              >\n                                <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold text-slate-500">\n                                  <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 shadow-sm">\n                                    <BookOpen className="h-3.5 w-3.5" style={{ color: activeCategory.color }} />\n                                    {/<ol[\\s>]/i.test(isEn ? art.answerEn : art.answerAr)\n                                      ? (isEn ? "Step-by-step guide" : "دليل خطوة بخطوة")\n                                      : (isEn ? "Help article" : "مقال مساعدة")}\n                                  </span>\n                                  <span className="hidden sm:inline text-slate-400">\n                                    {isEn ? "Permanent direct link available" : "رابط مباشر دائم متاح"}\n                                  </span>\n                                </div>\n                                <div className="flex flex-wrap items-center gap-2">\n                                  {art.videoUrl ? (\n                                    <a\n                                      href={art.videoUrl}\n                                      target="_blank"\n                                      rel="noreferrer"\n                                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-bold text-slate-600 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"\n                                    >\n                                      <PlayCircle className="h-3.5 w-3.5" style={{ color: activeCategory.color }} />\n                                      {isEn ? (art.videoTitleEn || "Watch video") : (art.videoTitleAr || "شاهد الفيديو")}\n                                    </a>\n                                  ) : null}\n                                  <button\n                                    type="button"\n                                    onClick={() => void handleCopyArticleLink(activeCategory.id, activeSection.id, art.id)}\n                                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-bold text-slate-600 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"\n                                  >\n                                    <Copy className="h-3.5 w-3.5" />\n                                    {copiedArticleId === art.id\n                                      ? (isEn ? "Copied" : "تم النسخ")\n                                      : (isEn ? "Copy link" : "نسخ الرابط")}\n                                  </button>\n                                  <a\n                                    href={helpArticlePath(lang, activeCategory.id, activeSection.id, art.id)}\n                                    target="_blank"\n                                    rel="noreferrer"\n                                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-bold text-slate-600 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"\n                                  >\n                                    <ExternalLink className="h-3.5 w-3.5" />\n                                    {isEn ? "Open article" : "فتح المقال"}\n                                  </a>\n                                </div>\n                              </div>\n                              <div className="article-content max-w-none" dangerouslySetInnerHTML={{ __html: isEn ? art.answerEn : art.answerAr }} />\n                            </AccordionContent>\n''',
    "article action bar and video hook",
)

if text == original:
    fail("No changes were produced.")

TARGET.write_text(text, encoding="utf-8")

print("[HELP-CENTER-P1] Applied successfully.")
print(f"[HELP-CENTER-P1] Updated: {TARGET}")
print("[HELP-CENTER-P1] Next: pnpm check && pnpm build")
