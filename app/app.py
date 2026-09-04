import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from src.hybrid_recommender import get_hybrid_recommendations
from src.explain import MovieExplainer
from src.feedback_handler import FeedbackHandler

# ============= PAGE CONFIG =============
st.set_page_config(
    page_title="CINEIQ - Movie Recommendations",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============= STYLING =============
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .recommendation-card {
        background: #f0f4ff;
        border-left: 4px solid #667eea;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    h1, h2, h3 {
        color: #667eea;
    }
    </style>
""", unsafe_allow_html=True)

# ============= LOAD DATA =============
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

@st.cache_data
def load_data():
    movies = pd.read_csv(DATA_DIR / "merged_movies.csv")
    ratings = pd.read_csv(DATA_DIR / "movielens" / "ratings.csv")
    return movies, ratings

movies, ratings = load_data()
explainer = MovieExplainer(movies)
feedback_handler = FeedbackHandler()

# ============= HEADER =============
st.markdown("# 🎬 CINEIQ - Personalized Movie Recommendations")
st.markdown("*Hybrid recommendation engine powered by collaborative filtering, content similarity, and sentiment analysis*")
st.divider()

# ============= SIDEBAR =============
with st.sidebar:
    st.header("⚙️ Settings")

    user_id = st.number_input(
        "Enter User ID",
        min_value=1,
        max_value=162541,
        value=1,
        step=1,
        help="MovieLens User ID (1-162541)"
    )

    st.divider()

    num_recommendations = st.slider(
        "Number of Recommendations",
        min_value=5,
        max_value=20,
        value=10,
        step=1
    )

    st.divider()

    st.subheader("About CINEIQ")
    st.info("""
    **CINEIQ** combines three recommendation signals:
    - **Collaborative Filtering** (70%): Learn from similar users
    - **Content Similarity** (30%): Find similar movies
    - **Sentiment** (20%): Use audience reviews

    **v2.0 Features:**
    - Better metrics tracking
    - User feedback system
    - Improved explainability
    """)

# ============= TABS =============
tab1, tab2, tab3 = st.tabs(["🎯 Recommendations", "📊 Your Taste Profile", "💬 Feedback"])

# ============= TAB 1: RECOMMENDATIONS =============
with tab1:
    col_left, col_right = st.columns([2, 1])

    with col_right:
        if st.button("🔄 Generate Recommendations", use_container_width=True, type="primary"):
            st.session_state.generate_recs = True

    if st.session_state.get('generate_recs', False):
        with st.spinner("🔄 Generating recommendations..."):
            try:
                recommendations = get_hybrid_recommendations(user_id, n=num_recommendations)
                st.session_state['last_recs'] = recommendations

                user_high_rated = ratings[
                    (ratings['userId'] == user_id) & (ratings['rating'] >= 4.0)
                ]['movieId'].values

                user_high_directors = movies[
                    movies['movieId'].isin(user_high_rated)
                ]['director'].dropna().unique().tolist()

                st.success(f"✅ Generated {len(recommendations)} recommendations")
                st.divider()

                # Display recommendations
                for idx, rec in enumerate(recommendations, 1):
                    movie_row = movies[movies['movieId'] == rec['movie_id']].iloc[0]

                    reason = explainer.explain(
                        movie_id=rec['movie_id'],
                        movie_row=movie_row,
                        user_high_rated_movie_ids=list(user_high_rated),
                        user_high_rated_directors=user_high_directors
                    )

                    with st.container():
                        col1, col2, col3 = st.columns([1, 3, 1.5])

                        with col1:
                            st.metric(f"#{idx}", f"{rec['final_score']:.2f}", delta=f"±{rec['sentiment_score']:.2f}")

                        with col2:
                            st.markdown(f"**{rec['title']}**")
                            st.caption(f"📂 Genres: {rec['genres']}")
                            st.caption(f"🎬 Director: {rec['director']}")
                            st.caption(f"💡 {reason}")

                        with col3:
                            col_hybrid, col_sent = st.columns(2)
                            with col_hybrid:
                                st.metric("Hybrid", f"{rec['hybrid_score']:.2f}")
                            with col_sent:
                                st.metric("Sentiment", f"{rec['sentiment_score']:.2f}")

                    st.divider()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ============= TAB 2: TASTE PROFILE =============
with tab2:
    user_ratings = ratings[ratings['userId'] == user_id]

    if len(user_ratings) == 0:
        st.warning("⚠️ No ratings found for this user")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Rated",
                len(user_ratings),
                help="Movies you've rated"
            )

        with col2:
            avg_rating = user_ratings['rating'].mean()
            st.metric(
                "Avg Rating",
                f"{avg_rating:.2f}",
                help="Your average rating given"
            )

        with col3:
            high_rated = len(user_ratings[user_ratings['rating'] >= 4.0])
            st.metric(
                "Liked (4+)",
                high_rated,
                help="Movies rated 4 or higher"
            )

        with col4:
            loved = len(user_ratings[user_ratings['rating'] >= 4.5])
            st.metric(
                "Loved (4.5+)",
                loved,
                help="Movies rated 4.5 or higher"
            )

        st.divider()

        # Genre analysis
        merged = user_ratings.merge(movies, on='movieId', how='left')
        genre_list = merged['genres'].str.split('|').explode()
        genre_counts = genre_list.value_counts().head(10)

        col_genre, col_director = st.columns(2)

        with col_genre:
            st.subheader("📚 Top Genres")
            fig_genre = px.bar(
                x=genre_counts.values,
                y=genre_counts.index,
                orientation='h',
                title="Your Top 10 Genres",
                labels={'x': 'Count', 'y': 'Genre'}
            )
            fig_genre.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_genre, use_container_width=True)

        with col_director:
            st.subheader("🎬 Top Directors")
            director_counts = merged[merged['director'] != "Unknown"]['director'].value_counts().head(10)
            if not director_counts.empty:
                fig_director = px.bar(
                    x=director_counts.values,
                    y=director_counts.index,
                    orientation='h',
                    title="Your Top 10 Directors",
                    labels={'x': 'Count', 'y': 'Director'}
                )
                fig_director.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_director, use_container_width=True)
            else:
                st.info("No director data available")

        # Genre preferences radar
        st.subheader("🎯 Genre Preference Radar")
        genre_top6 = genre_counts.head(6)

        if len(genre_top6) >= 3:
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=genre_top6.values.tolist() + [genre_top6.values.tolist()[0]],
                theta=genre_top6.index.tolist() + [genre_top6.index.tolist()[0]],
                fill='toself',
                name='Your Taste'
            ))
            fig_radar.update_layout(
                height=500,
                title="Your Top 6 Genre Preferences",
                showlegend=False
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # Timeline
        st.subheader("📅 Movies Watched by Decade")
        decades = merged['title'].str.extract(r'\((\d{4})\)', expand=False).astype(float)
        merged['decade'] = (decades // 10 * 10).astype('Int64')
        decade_counts = merged['decade'].value_counts().sort_index()

        fig_timeline = px.bar(
            x=decade_counts.index.astype(str),
            y=decade_counts.values,
            title="Your Watching Timeline",
            labels={'x': 'Decade', 'y': 'Count'}
        )
        fig_timeline.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_timeline, use_container_width=True)

# ============= TAB 3: FEEDBACK =============
with tab3:
    st.markdown("### 💬 Submit Feedback on Recommendations")
    st.markdown("Help us improve by providing feedback on movie recommendations!")

    col_left, col_right = st.columns(2)

    with col_left:
        feedback_user_id = st.number_input(
            "User ID",
            min_value=1,
            max_value=162541,
            value=user_id,
            key="feedback_uid"
        )

        # Prepare movie options (prioritize last generated recommendations if available)
        last_recs = st.session_state.get('last_recs', [])
        rec_movie_ids = [r['movie_id'] for r in last_recs]
        
        # Options list: recommended movies first, then remaining catalog
        if last_recs:
            rec_titles = [f"⭐ {r['title']} (ID: {r['movie_id']})" for r in last_recs]
            other_movies = movies[~movies['movieId'].isin(rec_movie_ids)].head(500)
            other_titles = [f"{row['title']} (ID: {row['movieId']})" for _, row in other_movies.iterrows()]
            movie_options = rec_titles + ["--- Other Movies ---"] + other_titles
        else:
            sample_movies = movies.head(500)
            movie_options = [f"{row['title']} (ID: {row['movieId']})" for _, row in sample_movies.iterrows()]

        selected_option = st.selectbox(
            "Select Movie to Review",
            options=[opt for opt in movie_options if opt != "--- Other Movies ---"],
            key="feedback_movie_select"
        )

        # Parse selected movie title and ID
        if selected_option:
            # Extract movie_id from string like "... (ID: 608)"
            import re
            match = re.search(r'\(ID:\s*(\d+)\)$', selected_option)
            if match:
                feedback_movie_id = int(match.group(1))
                clean_title = selected_option.replace(f" (ID: {feedback_movie_id})", "").replace("⭐ ", "")
                feedback_movie_title = clean_title
            else:
                feedback_movie_id = 1
                feedback_movie_title = selected_option
        else:
            feedback_movie_id = 1
            feedback_movie_title = "Unknown Movie"

    with col_right:
        feedback_type = st.selectbox(
            "How do you feel about this recommendation?",
            ["👍 Like", "👎 Dislike", "😐 Neutral"],
            key="feedback_type"
        )

        rating_given = st.slider(
            "Your Rating (optional)",
            min_value=1.0,
            max_value=5.0,
            value=3.0,
            step=0.5,
            key="feedback_rating"
        )

    comment = st.text_area(
        "Additional comments (optional)",
        placeholder="What did you think about this recommendation?",
        key="feedback_comment"
    )

    col_btn1, col_btn2 = st.columns([1, 4])

    with col_btn1:
        if st.button("📤 Submit Feedback", use_container_width=True, type="primary"):
            feedback_map = {"👍 Like": "like", "👎 Dislike": "dislike", "😐 Neutral": "neutral"}
            feedback_val = feedback_map[feedback_type]

            success = feedback_handler.add_feedback(
                user_id=int(feedback_user_id),
                movie_id=int(feedback_movie_id),
                movie_title=feedback_movie_title,
                rating_score=3.5,  # Placeholder, would come from recommendation
                final_score=3.8,   # Placeholder
                feedback=feedback_val,
                rating_given=rating_given,
                comment=comment
            )

            if success:
                st.success("✅ Feedback recorded! Thank you!")
            else:
                st.error("❌ Error recording feedback")

    st.divider()

    # Feedback statistics
    st.subheader("📈 Feedback Statistics")
    stats = feedback_handler.get_feedback_stats()

    if stats.get('total_feedback', 0) > 0:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Feedback", stats.get('total_feedback', 0))

        with col2:
            st.metric("Avg Rating", f"{stats.get('avg_rating_given', 0):.2f}")

        with col3:
            st.metric("Like Rate", f"{stats.get('like_percentage', 0):.1f}%")

        with col4:
            st.metric("Unique Users", stats.get('total_users', 0))

        st.divider()

        # Feedback breakdown
        feedback_col1, feedback_col2 = st.columns(2)

        with feedback_col1:
            feedback_data = pd.DataFrame({
                'Type': ['👍 Likes', '👎 Dislikes', '😐 Neutral'],
                'Count': [
                    stats.get('like_count', 0),
                    stats.get('dislike_count', 0),
                    stats.get('neutral_count', 0)
                ]
            })
            fig_feedback = px.pie(
                feedback_data,
                values='Count',
                names='Type',
                title="Feedback Distribution"
            )
            st.plotly_chart(fig_feedback, use_container_width=True)

        with feedback_col2:
            accuracy = feedback_handler.get_accuracy_metrics()
            if accuracy.get('total_rated_recommendations', 0) > 0:
                accuracy_data = pd.DataFrame({
                    'Metric': ['RMSE', 'MAE'],
                    'Value': [
                        accuracy.get('rmse', 0),
                        accuracy.get('mae', 0)
                    ]
                })
                fig_accuracy = px.bar(
                    accuracy_data,
                    x='Metric',
                    y='Value',
                    title="Prediction Accuracy"
                )
                st.plotly_chart(fig_accuracy, use_container_width=True)
            else:
                st.info("No rated recommendations yet")
    else:
        st.info("No feedback collected yet. Submit feedback to see statistics!")