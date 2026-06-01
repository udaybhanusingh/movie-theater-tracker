import streamlit as st
import requests

st.set_page_config(page_title="Gay Nights Theater Trips", page_icon="🎬")

st.title("Theater Trips")
st.write("Now playing movies from TMDb")

TMDB_ACCESS_TOKEN = st.secrets["TMDB_ACCESS_TOKEN"]

@st.cache_data(ttl=60 * 60)
def get_now_playing_movies():
    url = "https://api.themoviedb.org/3/movie/now_playing"

    headers = {
        "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
        "accept": "application/json",
    }

    params = {
        "language": "en-US",
        "region": "US",
        "page": 1,
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()["results"]

movies = get_now_playing_movies()

movie_titles = [
    f"{movie['title']} ({movie['release_date'][0:4]})"
    for movie in movies]

selected_movie = st.selectbox(
    "Choose a movie",
    movie_titles
)

st.write("Selected:", selected_movie)