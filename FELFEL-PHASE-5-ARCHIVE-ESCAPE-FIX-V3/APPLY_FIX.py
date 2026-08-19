#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

PATCH_ID = "FELFEL-PHASE-5-ARCHIVE-ESCAPE-FIX-V3"
BASELINE_SHA = "c8859eda1915af3d2abcdaf7261f62bc3ffd988e"
SERVICE = "server/services/felfel/felfelMeetingArchiveService.ts"
TEST = "server/services/felfel/felfelMeetingArchiveService.test.ts"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def run(*args: str) -> str:
    result = subprocess.run(list(args), cwd=root, text=True, capture_output=True