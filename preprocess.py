#!/usr/bin/env python3
"""Prepare scatter plot data from GoodReads file"""
from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

CSV_FILE = Path("GoodReads_100k_books.csv.xz")
JSON_FILE = Path("scatter_data.json")
MAX_ROWS = 5000
PERCENTILES = (0.005, 0.995)


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV_FILE, compression="xz", usecols=["pages", "desc", "reviews", "rating"])
    return df.dropna()


def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.assign(blurb=df["desc"].astype(str).str.len())
    for col in ["pages", "blurb", "reviews", "rating"]:
        low, high = df[col].quantile(PERCENTILES)
        df = df[df[col].between(low, high)]
    return df.sample(n=min(len(df), MAX_ROWS), random_state=42)


def save_json(df: pd.DataFrame) -> int:
    records = df[["pages", "blurb", "reviews", "rating"]].to_dict("records")
    JSON_FILE.write_text(json.dumps(records, separators=(",", ":")))
    return JSON_FILE.stat().st_size


def main() -> None:
    df = load()
    df = compute_stats(df)
    size = save_json(df)
    print(f"Wrote {size} bytes to {JSON_FILE}")


if __name__ == "__main__":
    main()
