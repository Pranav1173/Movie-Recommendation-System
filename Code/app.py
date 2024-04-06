import streamlit as st
import pandas as pd
import requests
import pickle
import os

# Load movies data and similarity scores
movies = pickle.load(open("movies_list.pkl", 'rb'))
similarity = pickle.load(open("similarity.pkl", 'rb'))

# Function to fetch movie details: poster and overview
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        poster_path = data.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None
        return poster_url
    else:
        return None

def update_movie_score(movie_id, feedback):
    scores_df = pd.read_csv("movies_scores.csv")
    if movie_id in scores_df['movie_id'].values:
        scores_df.loc[scores_df['movie_id'] == movie_id, 'score'] += 1 if feedback == "like" else -1
    else:
        scores_df = scores_df.append({"movie_id": movie_id, "score": 1 if feedback == "like" else -1}, ignore_index=True)
    scores_df.to_csv("movies_scores.csv", index=False)

def get_top_liked_movies():
    scores_df = pd.read_csv("movies_scores.csv")
    # Sort movies by score in descending order and take the top 5
    top_movies_df = scores_df.sort_values(by='score', ascending=False).head(5)
    top_movie_ids = top_movies_df['movie_id'].tolist()

    top_movie_details = [fetch_movie_details(movie_id) for movie_id in top_movie_ids]
    top_movie_names = [movies[movies['id'] == movie_id].title.iloc[0] for movie_id in top_movie_ids]

    return top_movie_names, top_movie_details

def log_watch_history(movie_id):
    new_entry = pd.DataFrame({'movie_id': [movie_id]})
    try:
        history_df = pd.read_csv("watch_history.csv")
        history_df = pd.concat([history_df, new_entry], ignore_index=True)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        history_df = new_entry
    history_df.to_csv("watch_history.csv", index=False)

def recommend_for_you():
    try:
        history_df = pd.read_csv("watch_history.csv")
        scores_df = pd.read_csv('movies_scores.csv')
        disliked_movie_ids = scores_df[scores_df['score'] < 0]['movie_id'].tolist()  # Assume negative scores are dislikes

        if not history_df.empty:
            last_movie_id = history_df.iloc[-1]['movie_id']
            movie_index = movies[movies['id'] == last_movie_id].index[0]
            distances = sorted(list(enumerate(similarity[movie_index])), reverse=True, key=lambda x: x[1])
            recommended_movie_names = []
            recommended_movie_posters = []
            for i in distances[1:]:  # Iterate through recommendations
                movie_id = movies.iloc[i[0]].id
                # Skip disliked movies
                if movie_id not in disliked_movie_ids:
                    recommended_movie_posters.append(fetch_movie_details(movie_id))
                    recommended_movie_names.append(movies.iloc[i[0]].title)
                if len(recommended_movie_names) == 5:  # Stop when we have 5 recommendations
                    break
            return recommended_movie_names, recommended_movie_posters
    except FileNotFoundError:
        return [], []
    return [], []


def recommend_movie_without_feedback(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].id
        recommended_movie_posters.append(fetch_movie_details(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)
    return recommended_movie_names, recommended_movie_posters

def recommend_movie_with_feedback(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[movie_index])), reverse=True, key=lambda x: x[1])
    recommended_movies = pd.DataFrame(distances[1:6], columns=['id', 'similarity'])
    recommended_movies['id'] = recommended_movies['id'].apply(lambda x: movies.iloc[x].id)
    scores_df = pd.read_csv('movies_scores.csv')
    recommended_movies = recommended_movies.join(scores_df.set_index('movie_id'), on='id')
    recommended_movies['score'] = recommended_movies['score'].fillna(0)
    recommended_movies = recommended_movies.sort_values(by=['score', 'similarity'], ascending=False)
    top_movies = recommended_movies.head(5)
    recommended_movie_details = top_movies['id'].apply(lambda x: fetch_movie_details(x)).tolist()
    recommended_movie_names = top_movies['id'].apply(lambda x: movies[movies['id'] == x].title.iloc[0]).tolist()
    return recommended_movie_names, recommended_movie_details

def recommend(selected_movie):
    if not os.path.exists("movies_scores.csv") or os.stat("movies_scores.csv").st_size == 0:
        return recommend_movie_without_feedback(selected_movie)
    else:
        try:
            scores_df = pd.read_csv("movies_scores.csv")
            if scores_df.empty:
                return recommend_movie_without_feedback(selected_movie)
            else:
                return recommend_movie_with_feedback(selected_movie)
        except pd.errors.EmptyDataError:
            return recommend_movie_without_feedback(selected_movie)

# Custom CSS styles
st.markdown(
'''<style>
img:hover {
    transform: scale(1.05);
    transition: transform .5s ease;
}
.stButton>button {
    width: 120px;
    height: 40px;
    margin: 5px 0;
}
</style>''', unsafe_allow_html=True)

# Streamlit UI setup
st.header("Movie Recommender System")
selected_movie = st.selectbox("Select a movie", movies['title'].values)

# Session state for recommend button
if "recommend_clicked" not in st.session_state:
    st.session_state.recommend_clicked = False

recommend_button_clicked = st.button("Recommend")

if recommend_button_clicked:
    movie_id = movies[movies['title'] == selected_movie].id.iloc[0]
    log_watch_history(movie_id)
    st.session_state.recommend_clicked = True

# Display recommendations if the recommend button was clicked
if st.session_state.recommend_clicked:
    names, details = recommend(selected_movie)
    cols = st.columns(len(names))
    for idx, col in enumerate(cols):
        with col:
            movie_id = movies[movies['title'] == names[idx]].id.iloc[0]
            st.text(names[idx])
            poster = details[idx]
            if poster:
                st.image(poster, use_column_width=True)
            if st.button("Like", key=f"like_{idx}"):
                update_movie_score(movie_id, "like")
                st.success("You liked " + names[idx])
            if st.button("Dislike", key=f"dislike_{idx}"):
                update_movie_score(movie_id, "dislike")
                st.error("You disliked " + names[idx])


# Display top 5 liked movies
st.header("Top 5 Liked Movies")
if os.path.exists("movies_scores.csv") and os.stat("movies_scores.csv").st_size != 0:
    top_names, top_details = get_top_liked_movies()
    cols = st.columns(len(top_names))
    for name, detail, col in zip(top_names, top_details, cols):
        with col:
            st.text(name)
            if detail:
                st.image(detail, use_column_width=True)

# Watch History Section
st.header("Your Watch History")
if os.path.exists("watch_history.csv") and os.stat("watch_history.csv").st_size != 0:
    history_df = pd.read_csv("watch_history.csv")
    # Ensure unique movie IDs and limit to the last 5 entries
    watched_movie_ids = history_df['movie_id'].drop_duplicates().tail(5)
    watched_movie_details = [fetch_movie_details(movie_id) for movie_id in watched_movie_ids]
    watched_movie_names = [movies[movies['id'] == movie_id].title.iloc[0] for movie_id in watched_movie_ids]
    if watched_movie_names:
        cols = st.columns(len(watched_movie_names))
        for idx, col in enumerate(cols):
            with col:
                st.text(watched_movie_names[idx])
                poster = watched_movie_details[idx]
                if poster:
                    st.image(poster, use_column_width=True)
    else:
        st.write("You haven't watched any movies yet!")
else:
    st.write("You haven't watched any movies yet!")


# Recommend for you Section
st.header("Recommended for You")
recommended_names, recommended_details = recommend_for_you()
if recommended_names:
    cols = st.columns(len(recommended_names))
    for idx, col in enumerate(cols):
        with col:
            st.text(recommended_names[idx])
            if recommended_details[idx]:
                st.image(recommended_details[idx], use_column_width=True)
else:
    st.write("Please watch movies to get recommendations!")