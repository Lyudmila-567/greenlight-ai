"""
Cleans and merges Kaggle's "Rotten Tomatoes movies and critic reviews dataset"
(stefanoleone992) into a simple, ClickHouse-friendly CSV of NEGATIVE reviews
only (review_type == 'Rotten') — these are the "audience complaints" Bob and
the Narrative Architect use to avoid clichés.

Expects two files from the Kaggle dataset:
  - rotten_tomatoes_movies.csv        (has: rotten_tomatoes_link, movie_title, genres, ...)
  - rotten_tomatoes_critic_reviews.csv (has: rotten_tomatoes_link, review_content, review_type, ...)

Output columns: movie_title, genre, review_text, review_type

Note: this table joins to historical_movies by TITLE (not movie_id), since
our historical_movies table (built from the other Kaggle dataset) has no
shared ID with this one. Bob's instructions should query/join on title.

Usage:
    python clean_reviews.py rotten_tomatoes_movies.csv rotten_tomatoes_critic_reviews.csv audience_reviews_clean.csv
"""

import sys
import pandas as pd


def extract_primary_genre(genres_raw):
    """rotten_tomatoes_movies.csv stores genres as a comma-separated string
    like 'Horror, Mystery & Suspense' — take the first one."""
    if pd.isna(genres_raw):
        return None
    first = str(genres_raw).split(",")[0].strip()
    return first if first else None


def main():
    if len(sys.argv) != 4:
        print("Usage: python clean_reviews.py <movies_csv> <critic_reviews_csv> <output_csv>")
        sys.exit(1)

    movies_path, reviews_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

    movies = pd.read_csv(movies_path, low_memory=False, on_bad_lines="skip")
    reviews = pd.read_csv(reviews_path, low_memory=False, on_bad_lines="skip")

    movies = movies[["rotten_tomatoes_link", "movie_title", "genres"]].copy()
    movies["genre"] = movies["genres"].apply(extract_primary_genre)
    movies = movies.dropna(subset=["movie_title", "genre"])

    reviews = reviews[["rotten_tomatoes_link", "review_content", "review_type"]].copy()
    reviews = reviews.dropna(subset=["review_content", "review_type"])

    # Only keep NEGATIVE reviews — these are the "audience complaints" we
    # actually need for the cliché-avoidance step. This also cuts the
    # dataset roughly in half before the merge, keeping the output manageable.
    reviews = reviews[reviews["review_type"].str.lower() == "rotten"]

    merged = reviews.merge(movies, on="rotten_tomatoes_link", how="inner")

    out = merged[["movie_title", "genre", "review_content", "review_type"]].rename(
        columns={"review_content": "review_text"}
    )

    out.to_csv(output_path, index=False)

    print(f"Kept {len(out)} negative reviews across {out['movie_title'].nunique()} movies.")
    print(f"Genre breakdown (by review count):\n{out['genre'].value_counts().head(15)}")
    print(f"\nSaved clean file to: {output_path}")


if __name__ == "__main__":
    main()
