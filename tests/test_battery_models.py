import json

import battery.models
from battery.models import load_charge_models


def test_load_charge_models_returns_defaults_when_model_is_missing(
    monkeypatch,
    tmp_path,
) -> None:
    model_file = tmp_path / "battery_charge_model.json"
    monkeypatch.setattr(battery.models, "MODEL_FILE", model_file)

    assert load_charge_models() == {
        "wired": {},
        "wireless": {},
    }


def test_load_charge_models_loads_existing_model(
    monkeypatch,
    tmp_path,
) -> None:
    model_file = tmp_path / "battery_charge_model.json"
    expected_model = {
        "wired": {
            "average": {
                "50": 120,
            },
        },
        "wireless": {
            "average": {
                "50": 180,
            },
        },
    }
    model_file.write_text(json.dumps(expected_model), encoding="utf-8")
    monkeypatch.setattr(battery.models, "MODEL_FILE", model_file)

    assert load_charge_models() == expected_model
