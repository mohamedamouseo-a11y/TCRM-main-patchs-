# TCRM AI Staff — Phase 13 Command Context Consistency V1

Baseline canonical main: `5f9cf7fe182126684454e7361cf119491e685b10`.

This is an implementation/build phase only. It does not perform final acceptance.

## Scope

Exactly four frontend page files:

- `client/src/pages/DarwishPage.tsx`
- `client/src/pages/ZaghloulV5Page.tsx`
- `client/src/pages/TaraAgentPage.tsx`
- `client/src/pages/FelfelPage.tsx`

Expected base blobs:

- Darwish: `9534afddf3b242c03bcf25f9c05568b277e735d5`
- Zaghloul: `2663ad9dc4d66c39349323225ea207894562bf78`
- Tara: `0268ea64d4a796b662e308de0a69f7252279d6b9`
- Felfel: `d2bb3032bf851e6070780bd86a69b66b86f32c1d`

## What changes

Adds a shared marker `data-ai-staff-command="context-v1"` to all four existing operational command cards.

Zaghloul receives a live Current Workspace badge while preserving its navigation-only Engagement Command and all 11 destinations.

Tara receives a live Current Workspace badge alongside its existing campaign/global scope badge while preserving `initialTab` behavior and all Control Center functionality. The label map uses the actual Tara workspace keys, including `voice` and `moderators`.

Darwish and Felfel only receive the shared command-family marker in this phase; their existing current-workspace context and command behavior are not changed.

## Safety

No backend, database, migration, API, routing, permission, customer-data, or Mautic change.

No business mutation is added to any command block. Existing Refresh Reliability and specialist handlers remain unchanged.

The guarded helper validates all four exact base blobs first and prepares all four source transformations before writing any application file, preventing a later anchor mismatch from leaving a partial Phase 13 apply.

Use:

```bash
python3 apply_ai_staff_command_context_consistency_v1.py --check
python3 apply_ai_staff_command_context_consistency_v1.py --apply
python3 apply_ai_staff_command_context_consistency_v1.py --verify
```

After build success, use TCRM Developer Hub from inside TCRM for Review Push and Auto Push to canonical `main`.
