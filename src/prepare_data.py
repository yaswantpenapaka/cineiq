"""
CINEIQ - Data Preparation Script
=================================
This script creates a clean, enriched movies dataset by reliably merging
MovieLens with TMDB metadata using links.csv (tmdbId).

Why this is better:
- Uses ID-based joining (tmdbId) instead of fragile title matching
- Extracts director during preparation (solves NaN issue in dashboard)
- Creates a clean, production-ready merged_movies.csv
"""

import pandas as pd
import ast
import os
from pathlib import Path

print("=" * 60)
print("CINEIQ Data Preparation Pipeline")
print("=" * 60)

# ================== CONFIG ==================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

MOVIELENS_DIR = DATA_DIR / "movielens"
TMDB_DIR = DATA_DIR / "tmdb"

OUTPUT_FILE = DATA_DIR / "merged_movies.csv"

print(f"\n[1/5] Loading datasets...")

# Load MovieLens data
movies = pd.read_csv(MOVIELENS_DIR / "movies.csv")
ratings = pd.read_csv(MOVIELENS_DIR / "ratings.csv")   # only for stats
links = pd.read_csv(MOVIELENS_DIR / "links.csv")

print(f"   MovieLens movies : {len(movies):,} rows")
print(f"   MovieLens links  : {len(links):,} rows")

# Load TMDB data
tmdb_movies = pd.read_csv(TMDB_DIR / "tmdb_5000_movies.csv")
tmdb_credits = pd.read_csv(TMDB_DIR / "tmdb_5000_credits.csv")

print(f"   TMDB movies      : {len(tmdb_movies):,} rows")
print(f"   TMDB credits     : {len(tmdb_credits):,} rows")

# ================== MERGE USING LINKS.CSV ==================
print("\n[2/5] Merging datasets using tmdbId (reliable join)...")

# Prepare links
links = links.dropna(subset=['tmdbId'])
links['tmdbId'] = links['tmdbId'].astype(int)

# Merge MovieLens movies with links
movies_with_tmdb = movies.merge(links[['movieId', 'tmdbId']], on='movieId', how='left')

print(f"   Movies with tmdbId: {movies_with_tmdb['tmdbId'].notna().sum():,} / {len(movies_with_tmdb):,}")

# Merge with TMDB movies on tmdbId
tmdb_movies_clean = tmdb_movies[['id', 'overview', 'keywords', 'vote_average']].copy()
tmdb_movies_clean = tmdb_movies_clean.rename(columns={'id': 'tmdbId'})

merged = movies_with_tmdb.merge(tmdb_movies_clean, on='tmdbId', how='left')

# Merge with TMDB credits on tmdbId
tmdb_credits_clean = tmdb_credits[['movie_id', 'cast', 'crew']].copy()
tmdb_credits_clean = tmdb_credits_clean.rename(columns={'movie_id': 'tmdbId'})

merged = merged.merge(tmdb_credits_clean, on='tmdbId', how='left')

print(f"   Final merged shape: {merged.shape}")

# ================== EXTRACT DIRECTOR (Cleanly) ==================
print("\n[3/5] Extracting director information...")

def extract_director(crew_str):
    """Safely extract director name from TMDB crew JSON"""
    if pd.isna(crew_str):
        return None
    try:
        crew = ast.literal_eval(crew_str)
        for person in crew:
            if person.get('job') == 'Director':
                return person.get('name')
        return None
    except (ValueError, SyntaxError, TypeError):
        return None

merged['director'] = merged['crew'].apply(extract_director)

director_count = merged['director'].notna().sum()
print(f"   Movies with director info: {director_count:,} ({director_count/len(merged)*100:.1f}%)")

# ================== OPTIONAL: Extract Top Cast ==================
print("\n[4/5] Extracting top cast (for future use)...")

def extract_top_cast(cast_str, top_n=3):
    if pd.isna(cast_str):
        return None
    try:
        cast_list = ast.literal_eval(cast_str)
        names = [p['name'] for p in cast_list[:top_n]]
        return ", ".join(names)
    except:
        return None

merged['top_cast'] = merged['cast'].apply(extract_top_cast)

# ================== CLEAN & SAVE ==================
print("\n[5/5] Cleaning and saving final dataset...")

# Select useful columns only
final_columns = [
    'movieId', 'tmdbId', 'title', 'genres',
    'director', 'top_cast',
    'overview', 'keywords', 'vote_average'
]

# Keep only columns that exist
final_df = merged[[col for col in final_columns if col in merged.columns]].copy()

# Fill missing values for cleaner downstream use
final_df['director'] = final_df['director'].fillna("Unknown")
final_df['top_cast'] = final_df['top_cast'].fillna("Unknown")
final_df['overview'] = final_df['overview'].fillna("")
final_df['keywords'] = final_df['keywords'].fillna("")

# Save
final_df.to_csv(OUTPUT_FILE, index=False)

print(f"\n✅ Successfully created: {OUTPUT_FILE}")
print(f"   Total movies in final dataset : {len(final_df):,}")
print(f"   Movies with director          : {(final_df['director'] != 'Unknown').sum():,}")
print(f"   Columns saved                 : {list(final_df.columns)}")

print("\n" + "=" * 60)
print("Data preparation completed successfully!")
print("You can now use 'data/merged_movies.csv' in your Streamlit app.")
print("=" * 60)