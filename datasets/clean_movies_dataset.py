"""
Cleans Kaggle's "The Movies Dataset" (movies_metadata.csv) into a simple,
ClickHouse-friendly CSV with columns: title, genre, budget_usd, revenue_usd.

The raw file stores `genres` as a stringified list of dicts, e.g.:
    [{'id': 28, 'name': 'Action'}, {'id': 12, 'name': 'Adventure'}]
This script extracts the FIRST genre name from that list as the movie's
primary genre, drops rows with missing/zero budget or revenue (useless for
financial benchmarking), and drops known malformed rows.

Usage:
    python clean_movies_dataset.py movies_metadata.csv historical_movies.csv
"""

import sys
import ast
import pandas as pd


def extract_primary_genre(genres_raw):
    """Parses the stringified list-of-dicts genres field and returns the
    first genre name, or None if parsing fails / list is empty."""
    if pd.isna(genres_raw):
        return None
    try:
        genres_list = ast.literal_eval(genres_raw)
        if isinstance(genres_list, list) and len(genres_list) > 0:
            return genres_list[0].get("name")
    except (ValueError, SyntaxError):
        return None
    return None


def main():
    if len(sys.argv) != 3:
        print("Usage: python clean_movies_dataset.py <input_csv> <output_csv>")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]

    # low_memory=False avoids dtype-guessing warnings on this messy file;
    # on_bad_lines="skip" drops the small number of structurally broken rows
    df = pd.read_csv(input_path, low_memory=False, on_bad_lines="skip")

    # Keep only the columns we actually need
    df = df[["title", "genres", "budget", "revenue"]].copy()

    # Extract a clean primary genre from the JSON-like genres column
    df["genre"] = df["genres"].apply(extract_primary_genre)

    # budget/revenue are sometimes strings, sometimes malformed — coerce to
    # numeric, turning anything unparseable into NaN
    df["budget_usd"] = pd.to_numeric(df["budget"], errors="coerce")
    df["revenue_usd"] = pd.to_numeric(df["revenue"], errors="coerce")

    # Drop rows that are useless for financial benchmarking: no title, no
    # genre, or zero/missing budget or revenue
    before = len(df)
    df = df.dropna(subset=["title", "genre", "budget_usd", "revenue_usd"])
    df = df[(df["budget_usd"] > 0) & (df["revenue_usd"] > 0)]
    after = len(df)

    df = df[["title", "genre", "budget_usd", "revenue_usd"]]
    df["budget_usd"] = df["budget_usd"].astype("int64")
    df["revenue_usd"] = df["revenue_usd"].astype("int64")

    df.to_csv(output_path, index=False)

    print(f"Read {before} rows, kept {after} clean rows with valid genre/budget/revenue.")
    print(f"Genre breakdown:\n{df['genre'].value_counts()}")
    print(f"\nSaved clean file to: {output_path}")


if __name__ == "__main__":
    main()
