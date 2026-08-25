# Phase 14 correction v1.1

The original Phase 14 helper stopped safely before writing because the generic Felfel transcript expression appeared three times in `FelfelPage.tsx`.

Use `apply_ai_staff_command_signal_truthfulness_v1_1.py` for the retry.

The corrective helper reuses the original guarded Phase 14 implementation for Darwish, Zaghloul, and Tara, but scopes the two Felfel signal replacements strictly to the existing `data-felfel-meeting-command="v9"` command-card region ending before `data-felfel-workspace="meeting-intelligence-v8"`.

This keeps the intended Phase 14 change limited to the Felfel Meeting Command tile values and does not alter other transcript/history counters elsewhere on the page.

Baseline canonical main remains `d047be42892a40d1085866388673cc74711e1ec4` with the same four base blobs. Implementation/build only; no final acceptance.