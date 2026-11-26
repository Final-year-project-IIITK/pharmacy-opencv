from __future__ import annotations

import math
import os
import sys
from datetime import date, timedelta
from types import SimpleNamespace
from pathlib import Path

from sklearn.metrics import mean_squared_error

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(ROOT)

from app.services.forecast import (
    _fallback_forecast,
    build_daily_series,
    forecast_consumption,
)


def make_records(start: date, end: date) -> list[SimpleNamespace]:
    records: list[SimpleNamespace] = []
    current = start
    index = 0
    while current <= end:
        weekly = 8.0 if current.weekday() < 5 else 5.0
        trend = index * 0.03
        quantity = max(0.0, weekly + trend + (2.0 if index % 14 < 7 else -1.0))
        records.append(SimpleNamespace(consumed_on=current, quantity=quantity))
        current += timedelta(days=1)
        index += 1
    return records


def main() -> None:
    start = date(2026, 1, 1)
    horizon = 30
    origins = 6
    xgboost_errors: list[float] = []
    fallback_errors: list[float] = []
    all_records = make_records(start, start + timedelta(days=269))

    for window in range(origins):
        split_index = 210 + window * 10
        split_date = all_records[split_index].consumed_on
        training = [record for record in all_records if record.consumed_on <= split_date]
        actual = all_records[min(split_index + horizon, len(all_records) - 1)].quantity

        result = forecast_consumption(training, (horizon,))
        predicted = float(result["points"][0]["predicted_quantity"])
        xgboost_errors.append(actual - predicted)

        fallback_predicted = _fallback_forecast(build_daily_series(training), horizon)
        fallback_errors.append(actual - fallback_predicted)

    xgboost_rmse = math.sqrt(mean_squared_error([0.0] * origins, xgboost_errors))
    fallback_rmse = math.sqrt(mean_squared_error([0.0] * origins, fallback_errors))

    print("Dataset: 270 days of deterministic synthetic daily consumption")
    print(f"Rolling-origin windows: {origins}")
    print(f"Horizon: {horizon} days")
    print(f"XGBoost/fallback service RMSE: {xgboost_rmse:.3f}")
    print(f"Fallback-only RMSE: {fallback_rmse:.3f}")
    print("Synthetic software-validation result; not evidence of real clinical demand accuracy.")


if __name__ == "__main__":
    main()
