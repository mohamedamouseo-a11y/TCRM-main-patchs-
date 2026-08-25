# Phase 13 Recovery — Pre-applied Target State

Use this only when production is still on canonical baseline `5f9cf7fe182126684454e7361cf119491e685b10` but the four Phase 13 page files are already modified and match the exact pre-applied target blobs below.

Expected dirty target blobs:

- Darwish: `74f9a2f1d82ecfc371818ec110d3b435de18e08a`
- Zaghloul: `0e5f936a82ea9ddf49e7e5368445299c6a709494`
- Tara: `6cfe876e92a8923455bc36569070da6d3f6429ae`
- Felfel: `c5461926d6ddca86cf2ce2e5f62daf3347ed9e32`

Expected diff scope and numstat:

- `client/src/pages/DarwishPage.tsx` — `1 1`
- `client/src/pages/FelfelPage.tsx` — `1 1`
- `client/src/pages/TaraAgentPage.tsx` — `7 2`
- `client/src/pages/ZaghloulV5Page.tsx` — `7 2`

The recovery verifier is read-only. It does not edit, reset, stash, discard, commit, push, or deploy anything.

Run from `/var/www/TCRM-MAIN`:

```bash
python3 <PATCH_PATH>/resume_phase13_from_preapplied_target.py
```

Only if it prints `RESUME_VERIFY=PASS` may the operator continue directly to build and the normal TCRM Developer Hub Review Push / Auto Push workflow. Do not run the original `--apply` helper again in this state.

If the verifier fails, stop and return evidence to ChatGPT. Never reset or discard the four existing modified files.
