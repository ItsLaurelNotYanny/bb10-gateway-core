"""Point the preset loader at the shared test fixtures before presets is imported."""

import os
from pathlib import Path

os.environ.setdefault("PRESETS_DIR", str(Path(__file__).parent / "presets.d"))
