#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import pathlib

BASE_HELPER = pathlib.Path(__file__).with_name("apply_ai_staff_command_signal_truthfulness_v1.py")
spec = importlib.util.spec_from_file_location("phase14_base_helper", BASE_HELPER)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load base helper: {BASE_HELPER}")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def patch_felfel(text: str) -> str:
    start_marker = 'data-felfel-meeting-command="v9" data-ai-staff-command="context-v1"'
    end_marker = 'data-felfel-workspace="meeting-intelligence-v8"'

    start = text.index(start_marker)
    end = text.index(end_marker, start)
    command_block = text[start:end]

    command_block = base.replace_once(
        command_block,
        start_marker,
        start_marker + ' data-ai-staff-signal-truth="v1"',
        "Felfel signal truth marker",
    )
    command_block = base.replace_once(
        command_block,
        'value: transcript?.segments?.length ?? 0',
        'value: meeting && transcriptQ.data === undefined ? "—" : (transcript?.segments?.length ?? 0)',
        "Felfel transcript command signal",
    )
    command_block = base.replace_once(
        command_block,
        'value: meetingsQ.data?.length ?? 0',
        'value: meetingsQ.data === undefined ? "—" : (meetingsQ.data?.length ?? 0)',
        "Felfel history command signal",
    )

    return text[:start] + command_block + text[end:]


base.patch_felfel = patch_felfel
base.PATCHERS["felfel"] = patch_felfel

if __name__ == "__main__":
    base.main()
