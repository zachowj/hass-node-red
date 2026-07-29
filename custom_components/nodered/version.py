"""Version info for Node-RED integration.

Single source of truth is ``manifest.json`` (HACS + release-please).
"""

from __future__ import annotations

import json
from pathlib import Path

__version__: str = json.loads(
    Path(__file__).with_name("manifest.json").read_text(encoding="utf-8")
)["version"]
