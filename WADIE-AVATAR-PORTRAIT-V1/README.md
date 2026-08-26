# WADIE AVATAR PORTRAIT V1

Purpose: replace the W letter/target placeholder inside Wadie AI Staff hero circle with Wadie portrait while keeping the existing premium AI Staff shell and status indicator.

Files:
- `WADIE-AVATAR-PORTRAIT-V1.patch`
- `wadie-avatar.jpg.b64`

Target repository:
`mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`

Target branch:
`main`

Apply:

```bash
mkdir -p client/src/assets/ai-staff
base64 -d /path/to/wadie-avatar.jpg.b64 > client/src/assets/ai-staff/wadie-avatar.jpg
git apply --check /path/to/WADIE-AVATAR-PORTRAIT-V1.patch
git apply /path/to/WADIE-AVATAR-PORTRAIT-V1.patch
```

Expected result:
- Wadie portrait appears inside the existing circular hero avatar.
- Existing amber integration-status dot remains unchanged.
- No GoMarble engine code is modified.
