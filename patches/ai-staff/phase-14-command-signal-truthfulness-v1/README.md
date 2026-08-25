# TCRM AI Staff — Phase 14 Command Signal Truthfulness V1

Baseline canonical main: `d047be42892a40d1085866388673cc74711e1ec4`.

Implementation/build phase only. No final acceptance, responsive/mobile acceptance, DevTools acceptance, or browser takeover.

## Scope

Exactly four frontend page files:

- `client/src/pages/DarwishPage.tsx`
- `client/src/pages/ZaghloulV5Page.tsx`
- `client/src/pages/TaraAgentPage.tsx`
- `client/src/pages/FelfelPage.tsx`

Expected base blobs:

- Darwish: `74f9a2f1d82ecfc371818ec110d3b435de18e08a`
- Zaghloul: `0e5f936a82ea9ddf49e7e5368445299c6a709494`
- Tara: `6cfe876e92a8923455bc36569070da6d3f6429ae`
- Felfel: `c5461926d6ddca86cf2ce2e5f62daf3347ed9e32`

## Purpose

The operational command layers currently render many not-yet-loaded signals as numeric zero. That can visually imply a real zero before the underlying query has returned.

Phase 14 adds `data-ai-staff-signal-truth="v1"` to each command layer and makes query-backed command signals show an em dash (`—`) while the source is still unavailable, then show the real numeric value once data exists.

This is display truthfulness only. A real loaded zero remains `0`.

### Darwish

All four Priority Command signals distinguish unloaded from loaded zero.

### Zaghloul

Audience and Inbox use both existing fallback sources before deciding the signal is unavailable. Automation and Team distinguish unloaded from loaded zero.

### Tara

Campaigns, Qualification, Follow-ups, and Knowledge distinguish unloaded query data from a real empty collection. Existing `initialTab` and scope behavior remain unchanged.

### Felfel

Transcript shows `—` only when a meeting exists and transcript data is still unavailable; no meeting remains a real `0`. Recent Meetings distinguishes unloaded history from a loaded empty list. Live Meeting and Meeting Intelligence semantics remain unchanged.

## Safety

No backend, API, database, migration, routing, permissions, customer-data, or Mautic changes.

No business mutations are added. Existing command layers remain navigation-only. Existing Refresh Reliability and specialist handlers remain unchanged.

Use:

```bash
python3 apply_ai_staff_command_signal_truthfulness_v1.py --check
python3 apply_ai_staff_command_signal_truthfulness_v1.py --apply
python3 apply_ai_staff_command_signal_truthfulness_v1.py --verify
```

After build success, use TCRM Developer Hub from inside TCRM for controlled Review Push and Auto Push to canonical `main`.
