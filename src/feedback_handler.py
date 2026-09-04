"""
CineIQ Feedback Management System
==================================
Handles collection, storage, and analysis of user feedback on recommendations.
Stores feedback in CSV for easy access and future model retraining.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import os


class FeedbackHandler:
    """
    Manage user feedback on movie recommendations.
    Stores feedback in CSV format for persistence.
    """

    def __init__(self, feedback_dir: Path = None):
        """
        Initialize feedback handler.

        Args:
            feedback_dir: Directory to store feedback CSV files.
                         If None, uses 'feedback' directory in project root.
        """
        if feedback_dir is None:
            feedback_dir = Path(__file__).parent.parent / "feedback"

        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.feedback_dir / "feedback_logs.csv"

        # Initialize CSV if doesn't exist
        if not self.feedback_file.exists():
            self._initialize_csv()

    def _initialize_csv(self):
        """Create empty feedback CSV with proper schema."""
        df = pd.DataFrame(columns=[
            'timestamp',
            'user_id',
            'movie_id',
            'movie_title',
            'rating_score',
            'final_score',
            'feedback',  # 'like', 'dislike', 'neutral'
            'rating_given',  # User's manual rating (1-5)
            'comment'
        ])
        df.to_csv(self.feedback_file, index=False)

    def add_feedback(
        self,
        user_id: int,
        movie_id: int,
        movie_title: str,
        rating_score: float,
        final_score: float,
        feedback: str,
        rating_given: Optional[float] = None,
        comment: str = ""
    ) -> bool:
        """
        Add feedback record for a recommendation.

        Args:
            user_id: User ID
            movie_id: Movie ID
            movie_title: Movie title
            rating_score: System's predicted rating
            final_score: System's final recommendation score
            feedback: 'like', 'dislike', or 'neutral'
            rating_given: User's actual rating (1-5)
            comment: User's comment on recommendation

        Returns:
            True if successful, False otherwise
        """
        if feedback not in ['like', 'dislike', 'neutral']:
            return False

        try:
            # Read existing data
            df = pd.read_csv(self.feedback_file)

            # Create new record
            new_record = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'movie_id': movie_id,
                'movie_title': movie_title,
                'rating_score': round(rating_score, 3),
                'final_score': round(final_score, 3),
                'feedback': feedback,
                'rating_given': rating_given,
                'comment': comment
            }

            # Append new record
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)

            # Save
            df.to_csv(self.feedback_file, index=False)
            return True

        except Exception as e:
            print(f"Error adding feedback: {e}")
            return False

    def get_feedback_stats(self) -> Dict:
        """
        Get summary statistics of feedback.

        Returns:
            Dictionary with feedback statistics
        """
        try:
            df = pd.read_csv(self.feedback_file)

            if len(df) == 0:
                return {
                    'total_feedback': 0,
                    'total_users': 0,
                    'total_movies': 0,
                    'like_count': 0,
                    'dislike_count': 0,
                    'neutral_count': 0,
                    'like_percentage': 0.0,
                    'avg_rating_given': 0.0
                }

            stats = {
                'total_feedback': len(df),
                'total_users': df['user_id'].nunique(),
                'total_movies': df['movie_id'].nunique(),
                'like_count': len(df[df['feedback'] == 'like']),
                'dislike_count': len(df[df['feedback'] == 'dislike']),
                'neutral_count': len(df[df['feedback'] == 'neutral']),
                'like_percentage': (len(df[df['feedback'] == 'like']) / len(df) * 100) if len(df) > 0 else 0.0,
                'avg_rating_given': df['rating_given'].mean() if df['rating_given'].notna().any() else 0.0
            }

            return stats

        except Exception as e:
            print(f"Error getting feedback stats: {e}")
            return {}

    def get_user_feedback(self, user_id: int) -> pd.DataFrame:
        """Get all feedback for a specific user."""
        try:
            df = pd.read_csv(self.feedback_file)
            return df[df['user_id'] == user_id]
        except Exception as e:
            print(f"Error getting user feedback: {e}")
            return pd.DataFrame()

    def get_movie_feedback(self, movie_id: int) -> pd.DataFrame:
        """Get all feedback for a specific movie."""
        try:
            df = pd.read_csv(self.feedback_file)
            return df[df['movie_id'] == movie_id]
        except Exception as e:
            print(f"Error getting movie feedback: {e}")
            return pd.DataFrame()

    def export_feedback(self, output_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
        """
        Export all feedback data.

        Args:
            output_path: Path to save exported CSV (optional)

        Returns:
            DataFrame with feedback data
        """
        try:
            df = pd.read_csv(self.feedback_file)

            if output_path:
                df.to_csv(output_path, index=False)
                print(f"Feedback exported to {output_path}")

            return df

        except Exception as e:
            print(f"Error exporting feedback: {e}")
            return None

    def get_accuracy_metrics(self) -> Dict:
        """
        Calculate accuracy metrics based on user ratings vs system scores.

        Returns:
            Metrics like RMSE, MAE between predicted and actual ratings
        """
        try:
            df = pd.read_csv(self.feedback_file)
            df = df[df['rating_given'].notna()]

            if len(df) == 0:
                return {
                    'total_rated_recommendations': 0,
                    'rmse': 0.0,
                    'mae': 0.0,
                    'correlation': 0.0
                }

            # Calculate RMSE
            mse = ((df['rating_score'] - df['rating_given']) ** 2).mean()
            rmse = mse ** 0.5

            # Calculate MAE
            mae = (df['rating_score'] - df['rating_given']).abs().mean()

            # Calculate correlation
            correlation = df['rating_score'].corr(df['rating_given'])

            return {
                'total_rated_recommendations': len(df),
                'rmse': round(rmse, 3),
                'mae': round(mae, 3),
                'correlation': round(correlation, 3)
            }

        except Exception as e:
            print(f"Error calculating accuracy metrics: {e}")
            return {}


def print_feedback_stats(handler: FeedbackHandler) -> None:
    """Pretty print feedback statistics."""
    stats = handler.get_feedback_stats()
    accuracy = handler.get_accuracy_metrics()

    print("\n" + "="*50)
    print("FEEDBACK STATISTICS")
    print("="*50)
    print(f"Total Feedback Entries...... {stats.get('total_feedback', 0)}")
    print(f"Unique Users................ {stats.get('total_users', 0)}")
    print(f"Unique Movies............... {stats.get('total_movies', 0)}")
    print(f"\nFeedback Distribution:")
    print(f"  👍 Likes..................... {stats.get('like_count', 0)}")
    print(f"  👎 Dislikes................. {stats.get('dislike_count', 0)}")
    print(f"  😐 Neutral.................. {stats.get('neutral_count', 0)}")
    print(f"  Like Rate................... {stats.get('like_percentage', 0):.1f}%")
    print(f"\nAccuracy Metrics:")
    print(f"  Total Rated Recommendations: {accuracy.get('total_rated_recommendations', 0)}")
    print(f"  RMSE........................ {accuracy.get('rmse', 0):.4f}")
    print(f"  MAE......................... {accuracy.get('mae', 0):.4f}")
    print(f"  Correlation................. {accuracy.get('correlation', 0):.4f}")
    print("="*50 + "\n")
