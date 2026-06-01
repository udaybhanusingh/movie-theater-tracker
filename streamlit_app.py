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
    accept_new_options = False
)

st.write("Adding to list:", selected_movie)

if st.button("Test spreadsheet connection"):
    worksheet = get_worksheet()
    worksheet.update_acell("A1", "Connected!")
    st.success("Spreadsheet connection worked.")