#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess

ROOT = pathlib.Path.cwd()

FILES = {
    "darwish": (pathlib.Path("client/src/pages/DarwishPage.tsx"), "2779e41b24972ae96b69f898d53e04139bfa9d4e"),
    "zaghloul": (pathlib.Path("client/src/pages/ZaghloulV5Page.tsx"), "d1f97d0ea81390b0df93828acbf1facfa41e5ec0"),
    "tara": (pathlib.Path("client/src/pages/TaraAgentPage.tsx"), "1354a816f999330e81486038232ee8c93df99cac"),
    "felfel": (pathlib.Path("client/src/pages/FelfelPage.tsx"), "fa4377ec27166a606398c23201b229d3055f8901"),
}


def git_blob(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def read(path: pathlib.Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: pathlib.Path, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def require_base() -> None:
    failures = []
    for name, (path, expected) in FILES.items():
        actual = git_blob(path)
        if actual != expected:
            failures.append(f"{name}: {path} expected {expected}, got {actual}")
    if failures:
        raise RuntimeError("Base blob mismatch:\n" + "\n".join(failures))


def patch_darwish(text: str) -> str:
    return replace_once(
        text,
        '<div dir={isRTL ? "rtl" : "ltr"} className="mx-auto max-w-[1660px] space-y-4 p-4 md:p-5 xl:p-6">',
        '<div data-ai-staff-shell="consistency-v1" dir={isRTL ? "rtl" : "ltr"} className="mx-auto max-w-[1660px] space-y-4 p-4 md:p-5 xl:p-6">',
        "darwish shared shell marker",
    )


def patch_zaghloul(text: str) -> str:
    return replace_once(
        text,
        '<div className="mx-auto flex max-w-[1600px] flex-col gap-5 p-4 md:p-6 xl:p-8" dir={isRTL ? "rtl" : "ltr"}>',
        '<div data-ai-staff-shell="consistency-v1" className="mx-auto flex max-w-[1660px] flex-col gap-4 p-4 md:p-5 xl:p-6" dir={isRTL ? "rtl" : "ltr"}>',
        "zaghloul shared shell geometry",
    )


def patch_tara(text: str) -> str:
    text = replace_once(
        text,
        '<div className="mx-auto max-w-[1660px] space-y-5 p-4 md:p-6 xl:p-8" dir={isRTL ? "rtl" : "ltr"}>',
        '<div data-ai-staff-shell="consistency-v1" className="mx-auto max-w-[1660px] space-y-4 p-4 md:p-5 xl:p-6" dir={isRTL ? "rtl" : "ltr"}>',
        "tara shared shell geometry",
    )
    text = replace_once(
        text,
        '<section className="rounded-[26px] border border-border/70 bg-card p-5 shadow-sm md:p-6">',
        '<section data-ai-staff-hero="consistency-v1" className="relative overflow-hidden rounded-[28px] border border-border/70 bg-gradient-to-br from-primary/10 via-card to-card p-5 shadow-[0_22px_64px_-40px_rgba(15,23,42,0.65)] md:p-7">',
        "tara hero family treatment",
    )
    text = replace_once(
        text,
        'className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-start"',
        'className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center"',
        "tara hero vertical alignment",
    )
    text = replace_once(
        text,
        '<div className="relative mx-auto h-[112px] w-[112px] shrink-0 sm:mx-0">',
        '<div className="relative mx-auto h-[152px] w-[152px] shrink-0 sm:mx-0">',
        "tara portrait footprint",
    )
    text = replace_once(
        text,
        '<p className="text-[10px] font-black uppercase tracking-[0.28em] text-primary">{taraIdentity.badge}</p>',
        '<p className="text-[11px] font-black uppercase tracking-[0.22em] text-primary">{taraIdentity.badge}</p>',
        "tara eyebrow typography",
    )
    text = replace_once(
        text,
        '<p className="mt-2 text-sm font-extrabold text-primary md:text-base">{taraIdentity.primaryTitle}</p>',
        '<p className="mt-2 text-lg font-black text-foreground">{taraIdentity.primaryTitle}</p>',
        "tara role hierarchy",
    )
    text = replace_once(
        text,
        '{manualRefreshPending ? (isRTL ? "جار التحديث..." : "Refreshing...") : (isRTL ? "تحديث" : "Refresh")}',
        '{manualRefreshPending ? (isRTL ? "جار التحديث..." : "Refreshing...") : (isRTL ? "تحديث البيانات" : "Refresh data")}',
        "tara refresh naming",
    )
    return text


def patch_felfel(text: str) -> str:
    text = replace_once(
        text,
        '<div className="mx-auto flex max-w-[1660px] flex-col gap-4 p-4 md:p-5 xl:p-6" dir={isRTL ? "rtl" : "ltr"}>',
        '<div data-ai-staff-shell="consistency-v1" className="mx-auto flex max-w-[1660px] flex-col gap-4 p-4 md:p-5 xl:p-6" dir={isRTL ? "rtl" : "ltr"}>',
        "felfel shared shell marker",
    )
    text = replace_once(
        text,
        'data-felfel-uxui="reference-v7" className="relative overflow-hidden rounded-[26px] border border-border/70 bg-gradient-to-br from-orange-500/10 via-card to-card shadow-[0_20px_60px_-38px_rgba(15,23,42,0.58)]"',
        'data-felfel-uxui="reference-v7" data-ai-staff-hero="consistency-v1" className="relative overflow-hidden rounded-[28px] border border-border/70 bg-gradient-to-br from-orange-500/10 via-card to-card shadow-[0_22px_64px_-40px_rgba(15,23,42,0.65)]"',
        "felfel hero family treatment",
    )
    text = replace_once(
        text,
        '<h1 className="text-3xl font-black tracking-[-0.035em] md:text-[38px]">{ar ? "فلفل" : "Felfel"}</h1>',
        '<h1 className="text-3xl font-black tracking-tight md:text-4xl">{ar ? "فلفل" : "Felfel"}</h1>',
        "felfel headline scale",
    )
    text = replace_once(
        text,
        '<p className="mt-1.5 text-base font-semibold text-muted-foreground">{ar ? "أخصائي ذكاء الاجتماعات بالذكاء الاصطناعي" : "AI Meeting Intelligence Specialist"}</p>',
        '<p className="mt-2 text-lg font-black text-foreground">{ar ? "أخصائي ذكاء الاجتماعات بالذكاء الاصطناعي" : "AI Meeting Intelligence Specialist"}</p>\n                <p className="mt-1 text-sm font-semibold text-muted-foreground">{ar ? "AI Meeting Intelligence Specialist" : "أخصائي ذكاء الاجتماعات بالذكاء الاصطناعي"}</p>',
        "felfel bilingual role hierarchy",
    )
    return text


PATCHERS = {
    "darwish": patch_darwish,
    "zaghloul": patch_zaghloul,
    "tara": patch_tara,
    "felfel": patch_felfel,
}


def apply_patch() -> None:
    require_base()
    for name, (path, _) in FILES.items():
        text = read(path)
        if 'data-ai-staff-shell="consistency-v1"' in text:
            raise RuntimeError(f"{name}: Phase 8 marker already present")
        patched = PATCHERS[name](text)
        write(path, patched)
        print(f"{name.upper()}_TARGET_BLOB={git_blob(path)}")
    print("APPLY=PASS")


def verify() -> None:
    required_by_agent = {
        "darwish": [
            'data-ai-staff-shell="consistency-v1"',
            'data-darwish-workspace="supervisor-v3"',
            'data-ai-staff-refresh="darwish-v1"',
        ],
        "zaghloul": [
            'data-ai-staff-shell="consistency-v1"',
            'data-zaghloul-workspace="grouped-nav-v2"',
            'data-ai-staff-refresh="zaghloul-v1"',
            'max-w-[1660px] flex-col gap-4 p-4 md:p-5 xl:p-6',
        ],
        "tara": [
            'data-ai-staff-shell="consistency-v1"',
            'data-ai-staff-hero="consistency-v1"',
            'data-tara-workspace="control-center-v2"',
            'data-ai-staff-refresh="tara-v1"',
            'h-[152px] w-[152px]',
            'text-lg font-black text-foreground">{taraIdentity.primaryTitle}',
            '"تحديث البيانات" : "Refresh data"',
        ],
        "felfel": [
            'data-ai-staff-shell="consistency-v1"',
            'data-ai-staff-hero="consistency-v1"',
            'data-felfel-workspace="meeting-intelligence-v8"',
            'data-ai-staff-refresh="felfel-v1"',
            'TCRM_FELFEL_REFRESH_COMPLETION_V1',
            'tracking-tight md:text-4xl',
            'AI Meeting Intelligence Specialist" : "أخصائي ذكاء الاجتماعات بالذكاء الاصطناعي"',
        ],
    }
    for name, (path, _) in FILES.items():
        text = read(path)
        missing = [item for item in required_by_agent[name] if item not in text]
        if missing:
            raise RuntimeError(f"{name}: missing Phase 8/preserved markers: {missing}")
        if text.count('data-ai-staff-shell="consistency-v1"') != 1:
            raise RuntimeError(f"{name}: shared shell marker count mismatch")
        print(f"{name.upper()}_TARGET_BLOB={git_blob(path)}")
    print("VERIFY=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if args.check:
        require_base()
        for name, (_, expected) in FILES.items():
            print(f"{name.upper()}_BASE_BLOB={expected}")
        print("CHECK=PASS")
        return
    if args.apply:
        apply_patch()
        return
    verify()


if __name__ == "__main__":
    main()
