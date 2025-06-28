import json
from pathlib import Path

import pandas as pd


def main() -> None:
    """Prepare dataset for visualization."""
    csv = Path("GoodReads_100k_books.csv.xz")
    if not csv.exists():
        print("Dataset missing")
        return
    df = pd.read_csv(csv)
    df = df[["pages", "desc", "reviews", "rating"]].copy()
    df["pages"] = pd.to_numeric(df["pages"], errors="coerce")
    df["reviews"] = pd.to_numeric(df["reviews"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["blurb"] = df["desc"].astype(str).str.len()
    df = df.dropna()

    cols = ["pages", "blurb", "reviews", "rating"]
    mask = pd.Series(True, index=df.index)
    for c in cols:
        low, high = df[c].quantile([0.005, 0.995])
        mask &= df[c].between(low, high)
    df = df[mask]

    n = min(5000, len(df))
    df = df.sample(n=n, random_state=42)
    out = df[cols].to_dict("records")
    data = json.dumps(out, separators=(",", ":"))
    path = Path("scatter_data.json")
    path.write_text(data)
    print(len(data.encode()), "bytes")


if __name__ == "__main__":
    main()
