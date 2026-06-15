"""
CINEIQ Explainability Module (LIME + Rule-based)
================================================
Provides human-readable explanations for recommendations.
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

try:
    from lime.lime_text import LimeTextExplainer
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    print("Warning: 'lime' not installed. Using rule-based explanations only.")


class MovieExplainer:
    def __init__(self, movies_df):
        self.movies_df = movies_df.copy()
        self.movies_df['content'] = (
            self.movies_df['genres'].fillna('') + ' ' +
            self.movies_df['overview'].fillna('') + ' ' +
            self.movies_df['keywords'].fillna('')
        )
        self.tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        self.tfidf_matrix = self.tfidf.fit_transform(self.movies_df['content'])

    def get_rule_based_explanation(self, movie_row, user_high_rated_directors):
        """Simple but effective rule-based explanation"""
        director = movie_row.get('director', 'Unknown')
        genres = movie_row.get('genres', '')

        if director != "Unknown" and director in user_high_rated_directors:
            return f"You seem to like {director}'s movies"
        elif genres:
            return f"Matches genres you watch often: {genres.split('|')[0]}"
        else:
            return "Based on your rating patterns and similar users"

    def get_lime_explanation(self, movie_id, user_high_rated_movie_ids, num_features=5):
        """
        Use LIME to explain content similarity (requires 'lime' package).
        """
        if not LIME_AVAILABLE:
            return None

        try:
            movie_idx = self.movies_df[self.movies_df['movieId'] == movie_id].index[0]
            movie_content = self.movies_df.loc[movie_idx, 'content']

            def predict_fn(texts):
                tfidf_texts = self.tfidf.transform(texts)
                liked_indices = self.movies_df[self.movies_df['movieId'].isin(user_high_rated_movie_ids)].index
                
                if len(liked_indices) == 0:
                    return np.array([[0.5, 0.5]] * len(texts))
                
                liked_vec = self.tfidf_matrix[liked_indices].mean(axis=0)
                sims = cosine_similarity(tfidf_texts, liked_vec)
                probs = (sims + 1) / 2
                return np.hstack([1 - probs, probs])

            explainer = LimeTextExplainer(class_names=['Not Similar', 'Similar'])
            exp = explainer.explain_instance(
                movie_content, 
                predict_fn, 
                num_features=num_features, 
                num_samples=300
            )
            
            explanation_list = exp.as_list()
            positive_features = [word for word, weight in explanation_list if weight > 0][:4]
            
            if positive_features:
                return f"Because it shares themes like: {', '.join(positive_features)}"
            return None

        except Exception:
            return None

    def explain(self, movie_id, movie_row, user_high_rated_movie_ids, user_high_rated_directors):
        """
        Main method: Try LIME first, fall back to rule-based.
        """
        # Try LIME explanation
        lime_exp = self.get_lime_explanation(movie_id, user_high_rated_movie_ids)
        if lime_exp:
            return lime_exp

        # Fallback to rule-based
        return self.get_rule_based_explanation(movie_row, user_high_rated_directors)