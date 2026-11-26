from __future__ import annotations

import math
import os
import sys
from pathlib import Path
from statistics import mean

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(ROOT)

from app.main import app


def percentile(values: list[float], percentage: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentage
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def main() -> None:
    request_count = 100
    with TestClient(app) as client:
        measured: list[float] = []
        for _ in range(request_count):
            response = client.get("/health")
            response.raise_for_status()
            measured.append(float(response.headers["X-Response-Time-Ms"]))

    print(f"Endpoint: GET /health")
    print(f"Requests: {request_count}")
    print(f"Average response time: {mean(measured):.3f} ms")
    print(f"p95 response time: {percentile(measured, 0.95):.3f} ms")
    print("Environment: in-process FastAPI TestClient; not representative of production network load")


if __name__ == "__main__":
    main()
