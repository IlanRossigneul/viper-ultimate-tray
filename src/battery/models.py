import json
from typing import Any

from config.paths import MODEL_FILE


def load_charge_models() -> dict[str, dict[str, Any]]:
    if not MODEL_FILE.exists():
        return {"wired": {}, "wireless": {}}

    with MODEL_FILE.open(
        "r",
        encoding="utf-8",
    ) as model_file:
        return json.load(model_file)
