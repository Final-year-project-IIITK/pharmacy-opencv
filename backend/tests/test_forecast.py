from datetime import date, timedelta
from types import SimpleNamespace

from app.services.forecast import forecast_consumption


def test_forecast_returns_all_supported_horizons() -> None:
    records = [
        SimpleNamespace(
            consumed_on=date(2026, 1, 1) + timedelta(days=index),
            quantity=float(10 + (index % 7)),
        )
        for index in range(180)
    ]

    result = forecast_consumption(records, (30, 60, 90))

    assert result["recent_daily_avg"] > 0
    assert [point["horizon_days"] for point in result["points"]] == [30, 60, 90]
    assert all(point["predicted_quantity"] >= 0 for point in result["points"])
    assert result["recommendation"] >= 0


def test_forecast_fallback_handles_no_history() -> None:
    result = forecast_consumption([], (30, 60, 90))

    assert result["recent_daily_avg"] == 0
    assert [point["predicted_quantity"] for point in result["points"]] == [0.0, 0.0, 0.0]
    assert result["recommendation"] == 0
