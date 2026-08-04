import json
from typing import Any

from config.paths import MODEL_FILE


def load_charge_models() -> list[dict[str, Any]]:
    with MODEL_FILE.open(
        "r",
        encoding="utf-8",
    ) as model_file:
        return json.load(model_file)["sources"]