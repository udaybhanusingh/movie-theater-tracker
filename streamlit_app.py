import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gay Nights Theater Trips", page_icon="🎬")

st.title("Theater Trips")
st.write("Now playing movies from TMDb")

TMDB_ACCESS_TOKEN = st.secrets["TMDB_ACCESS_TOKEN"]
GOOGLE_SHEET_ID = st.secrets["GOOGLE_SHEET_ID"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_worksheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)

    return spreadsheet.sheet1

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

members = ['Uday','Francisco','Abel','John','Yael','Rory','Rodrigo','Ricky','Mercedes','Tyra']
members.sort()

selected_member = st.selectbox(
    "Who are you?:",
    members,
    index=None,
    placeholder="Select...",
    accept_new_options = False
)

selected_movie = st.selectbox(
    "What do you wanna watch?",
    movie_titles,
    index=None,
    placeholder="Select...",
    accept_new_options = False,
    disabled = selected_member is None
)

movie_lookup = {
    f"{movie['title']} ({movie['release_date'][0:4]})": movie
    for movie in movies
}

if st.button("Add to list", disabled=selected_member is None or selected_movie is None):
    worksheet = get_worksheet()
    movie = movie_lookup[selected_movie]

    all_values = worksheet.get_all_values()
    headers = all_values[0]

    tmdb_id_col = headers.index("tmdb_id") + 1
    member_col = headers.index(selected_member) + 1

    movie_row = None

    for row_number, row in enumerate(all_values[1:], start=2):
        if row[tmdb_id_col - 1] == str(movie["id"]):
            movie_row = row_number
            break

    if movie_row is None:
        poster_url = ""
        if movie.get("poster_path"):
            poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"

        new_row = [""] * len(headers)
        new_row[headers.index("tmdb_id")] = movie["id"]
        new_row[headers.index("title")] = movie["title"]
        new_row[headers.index("release_date")] = movie.get("release_date", "")
        new_row[headers.index("poster_url")] = poster_url

        worksheet.append_row(new_row)

        all_values = worksheet.get_all_values()
        movie_row = len(all_values)
    
    worksheet.update_cell(movie_row, member_col, "TRUE")

    st.success(f"Added {movie['title']} for {selected_member}.")