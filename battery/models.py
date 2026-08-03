import json

from config.paths import MODEL_FILE


def load_charge_models():
    with MODEL_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["sources"]