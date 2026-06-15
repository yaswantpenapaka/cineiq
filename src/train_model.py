"""
CINEIQ - Model Training Script
==============================
Trains SVD collaborative filtering model using Surprise library.
Saves the model for use in the recommendation system.
"""

import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from surprise import accuracy
import pickle
from pathlib import Path

print("=" * 60)
print("CINEIQ Model Training")
print("=" * 60)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RATINGS_FILE = DATA_DIR / "movielens" / "ratings.csv"
MODEL_FILE = BASE_DIR / "models" / "svd_model.pkl"

# Create models directory if it doesn't exist
MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)

print("\n[1/4] Loading ratings data...")
ratings = pd.read_csv(RATINGS_FILE)
print(f"   Loaded {len(ratings):,} ratings from {ratings['userId'].nunique():,} users")

# Prepare data for Surprise
reader = Reader(rating_scale=(0.5, 5.0))
data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)

# Split into train and test
trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

print("\n[2/4] Training SVD model...")
model = SVD(
    n_factors=100,
    n_epochs=25,
    lr_all=0.005,
    reg_all=0.02,
    random_state=42
)
model.fit(trainset)

print("\n[3/4] Evaluating model...")
predictions = model.test(testset)
rmse = accuracy.rmse(predictions)
print(f"   RMSE on test set: {rmse:.4f}")

print("\n[4/4] Saving model...")
with open(MODEL_FILE, 'wb') as f:
    pickle.dump(model, f)

print(f"\n✅ Model saved successfully at: {MODEL_FILE}")
print("=" * 60)