"""Application runner for Strait of Hormuz Economic Risk Intelligence."""

from __future__ import annotations

import argparse

import uvicorn

from src.ba_artifacts import generate_all_ba_artifacts
from src.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Strait of Hormuz Risk Intelligence Platform")
    parser.add_argument("--refresh", action="store_true", help="Refresh live EIA/FRED/Yahoo inputs when reachable")
    parser.add_argument("--ba-only", action="store_true", help="Build ETL and BA deliverables without starting server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8004)
    args = parser.parse_args()

    stats = run_pipeline(refresh=args.refresh)
    print(f"Pipeline loaded -> {stats}")
    ba_out = generate_all_ba_artifacts()
    print(f"BA artifacts generated -> {list(ba_out.keys())}")

    if not args.ba_only:
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
