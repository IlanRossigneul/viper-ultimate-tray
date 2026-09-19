from battery.estimation import get_charge_estimation


def test_get_charge_estimation_returns_none_for_unknown_source() -> None:
    charge_models = {
        "wireless": {
            "average": {
                "50": 600,
            },
        },
    }

    assert get_charge_estimation(50, "wired", charge_models) is None


def test_get_charge_estimation_returns_none_without_transitions() -> None:
    charge_models = {
        "wireless": {
            "average": {},
        },
    }

    assert get_charge_estimation(50, "wireless", charge_models) is None


def test_get_charge_estimation_counts_current_transition_as_half() -> None:
    charge_models = {
        "wireless": {
            "average": {
                "50": 600,
            },
        },
    }

    assert (
        get_charge_estimation(50, "wireless", charge_models)
        == "5 min environ avant pleine recharge"
    )


def test_get_charge_estimation_counts_subsequent_transitions_fully() -> None:
    charge_models = {
        "wireless": {
            "average": {
                "51": 600,
                "52": 1200,
            },
        },
    }

    assert (
        get_charge_estimation(50, "wireless", charge_models)
        == "30 min environ avant pleine recharge"
    )


def test_get_charge_estimation_combines_current_and_subsequent_transitions() -> None:
    charge_models = {
        "wireless": {
            "average": {
                "50": 600,
                "51": 600,
                "52": 1200,
            },
        },
    }

    assert (
        get_charge_estimation(50, "wireless", charge_models)
        == "35 min environ avant pleine recharge"
    )


def test_get_charge_estimation_formats_hours_and_minutes() -> None:
    charge_models = {
        "wireless": {
            "average": {
                "50": 3600,
                "51": 3600,
            },
        },
    }

    assert (
        get_charge_estimation(50, "wireless", charge_models)
        == "1 h 30 min environ avant pleine recharge"
    )


def test_get_charge_estimation_formats_exact_hours() -> None:
    charge_models = {
        "wireless": {
            "average": {
                "50": 7200,
            },
        },
    }

    assert (
        get_charge_estimation(50, "wireless", charge_models)
        == "1 h environ avant pleine recharge"
    )


def test_get_charge_estimation_normalizes_rounded_sixty_minutes() -> None:
    charge_models = {
        "wireless": {
            "average": {
                "50": 3599,
            },
        },
    }

    assert (
        get_charge_estimation(50, "wireless", charge_models)
        == "30 min environ avant pleine recharge"
    )
