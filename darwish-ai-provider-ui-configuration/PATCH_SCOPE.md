# Darwish AI Provider UI Configuration Patch

Base commit: `30310fa744deb43583db73865dd21c755442cb9d`

## Scope

Frontend-only UI enhancement. No backend, migration, seed, runtime provider creation, deployment, or restart.

Changed paths:
- `client/src/pages/AdminSettings.tsx` — switches Darwish settings tab to the V2 UI component.
- `client/src/components/DarwishAiProvidersSettingsTabV2.tsx` — new premium UI configuration surface.

## UI capabilities

- Valid empty/not-configured state with fail-closed messaging.
- Provider add/edit/delete/enable-disable.
- OpenAI-compatible / Chat Completions adapter selection.
- Provider Base URL and advanced runtime configuration: API-key requirement, secret-key name, chat-completions path, temperature, max tokens.
- Model add/edit/delete/enable-disable with optional temperature/max tokens.
- Encrypted secret set/replace/remove; saved values are never rendered back.
- Routing policies restricted to `darwish.intelligence` and `darwish.reply_draft`.
- Policy add/edit/delete/enable-disable; selection strategy, attempts and timeout.
- Routing target add/edit/delete/enable-disable; provider/model filtering, priority, weight and timeout.
- Visible fallback order and client-side route-readiness status.
- Safe runtime monitoring counters via existing monitoring endpoint.
- No automatic provider/model/policy/target/secret creation.
