import streamlit as st
import requests
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import date, timedelta

st.set_page_config(page_title="Gay Nights Theater Trips", page_icon="🎬")

st.markdown("""
<div style="
    padding: 0.25rem 2rem;
    border-radius: 1rem;
    background: linear-gradient(135deg, rgba(255,105,180,0.18), rgba(138,43,226,0.16));
    border: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 1rem;
">
<h1 style="margin-bottom: 0.5rem;">Gay Nights at AMC 🍿</h1>
<p style="font-size: 1.1rem;">
👤 <b>Pick your name</b> and 🎬 <b>add a movie</b> you'd like to watch.<br>
❌ Remove selections anytime.<br>
🕒 Updated daily: movies currently showing or being released in the next 90 days.<br>
🔥 See <b>Most Requested</b> below to find the group's top picks.
</p>
</div>
""", unsafe_allow_html=True)

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

@st.cache_data(ttl=60 * 60)
def get_upcoming_movies():
    url = "https://api.themoviedb.org/3/discover/movie"

    headers = {
        "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
        "accept": "application/json",
    }

    today = date.today()
    ninety_days_from_now = today + timedelta(days=90)

    params = {
        "language": "en-US",
        "region": "US",
        "page": 1,
        "sort_by": "primary_release_date.asc",
        "release_date.gte": today.isoformat(),
        "release_date.lte": ninety_days_from_now.isoformat(),
        "with_release_type": "2|3",
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    total_pages = response.json().get("total_pages", 1)
    max_pages = min(total_pages, 12)
    all_movies = response.json().get("results", [])

    for page in range(2, max_pages + 1):
        params["page"] = page
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        all_movies.extend(response.json().get("results", []))

    return all_movies

upcoming_movies = get_upcoming_movies()

now_showing_movie_titles = [
    f"{movie['title']} ({movie['release_date'][0:4]})"
    for movie in movies]

upcoming_movie_titles = [
    f"{movie['title']} ({movie.get('release_date', 'Unknown')[:4]})"
    for movie in upcoming_movies]

all_movies = movies + upcoming_movies

movie_lookup = {
    f"{movie['title']} ({movie['release_date'][:4]})": movie
    for movie in all_movies}

movie_titles = sorted(movie_lookup.keys())

members = ['Uday','Francisco','Abel','John','Yael','Rory','Rodrigo','Ricky','Mercedes','Tyra']
members.sort()

with st.container(border=True):

    selected_member = st.selectbox(
        "Who are you?:",
        members,
        index=None,
        placeholder="Select...",
        accept_new_options = False
    )

    def get_user_selection(selected_member):
        worksheet = get_worksheet()
        all_values = worksheet.get_all_values()

        headers = all_values[0]

        title_col = headers.index("title")
        member_col = headers.index(selected_member)

        selections = []

        for row_number, row in enumerate(all_values[1:], start=2):
            if len(row) > member_col and str(row[member_col]).upper() == "TRUE":
                selections.append({
                    "title": row[title_col],
                    "poster_url": row[headers.index("poster_url")] if "poster_url" in headers else "",
                    "row_number": row_number,
                    "member_col": member_col + 1
                })

        return selections

    selected_movie = st.selectbox(
        "What do you wanna watch?",
        movie_titles,
        index=None,
        placeholder="Select...",
        accept_new_options = False,
        disabled = selected_member is None
    )

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
        
        if worksheet.cell(movie_row, member_col).value != "TRUE":
            worksheet.update_cell(movie_row, member_col, "TRUE")
        else:
            st.warning(f"{selected_member} has already added {movie['title']}.")
            st.stop()

        st.success(f"Added {movie['title']} for {selected_member}.")

if selected_member is not None:
    st.subheader(f"{selected_member}'s Current Selections:")

    user_selections = get_user_selection(selected_member)

    if user_selections:
        for selection in user_selections:
            text_col, button_col = st.columns([0.99, 0.01],gap="small",vertical_alignment="top",width=400)

            with text_col:
                st.markdown(
                    f"""
                    <div style="
                    padding: 0.3rem 0.75rem;
                    margin-bottom: 0.05rem;
                    border-radius: 0.45rem;
                    border: 1px solid rgba(250,250,250,0.12);
                    background-color: rgba(250,250,250,0.04);
                    font-size: 0.95rem;
                ">
                        🎬 {selection["title"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with button_col:
                if st.button(
                    "",
                    icon="❌",
                    width="content",
                    type="tertiary",
                    key=f"remove_{selected_member}_{selection['row_number']}"
                ):
                    worksheet = get_worksheet()

                    worksheet.update_cell(
                        selection["row_number"],
                        selection["member_col"],
                        ""
                    )

                    st.rerun()

    else:
        st.write("You haven't added any movies yet.")

st.divider()

def get_most_requested(limit=4):
    worksheet = get_worksheet()
    all_values = worksheet.get_all_values()

    headers = all_values[0]

    title_col = headers.index("title")
    poster_col = headers.index("poster_url")

    member_cols = [
        headers.index(member)
        for member in members
        if member in headers
    ]

    movie_counts = []

    for row in all_values[1:]:
        requesters = []

        for col in member_cols:
            if len(row) > col and str(row[col]).upper() == "TRUE":
                requesters.append(headers[col])

        request_count = len(requesters)

        if request_count > 0:
            movie_counts.append({
                "title": row[title_col],
                "poster_url": row[poster_col],
                "request_count": request_count,
                "requesters": requesters
            })

    movie_counts.sort(
        key=lambda movie: movie["request_count"],
        reverse=True
    )

    return movie_counts[:limit]


st.subheader("Most Requested:")

most_requested = get_most_requested(limit=4)

if most_requested:
    cols = st.columns(4, gap="xxsmall",border=True)

    for i, movie in enumerate(most_requested):
        with cols[i]:
            st.image(
                movie["poster_url"],
                width=150
            )

            st.caption(movie["title"])

            request_word = (
                "Request"
                if movie["request_count"] == 1
                else "Requests"
            )

            with st.popover(
                f"👥 {movie['request_count']} {request_word}"
            ):
                for requester in movie["requesters"]:
                    st.write(f"👤 {requester}")

else:
    st.write("No movies requested yet.")

st.iframe(
    "https://tenor.com/embed/27063004",
    height=350
)

worksheet = get_worksheet()
all_values = worksheet.get_all_values()

df = pd.DataFrame(
    all_values[1:],
    columns=all_values[0]
)

display_df = df[
    ["title"] + members
]

display_df = display_df.rename(columns={"title": ""})

for row in display_df.itertuples():
    for member in members:
        value = getattr(row, member)
        if str(value).upper() == "TRUE":
            display_df.at[row.Index, member] = "✅"
        else:
            display_df.at[row.Index, member] = ""

st.dataframe(
    display_df,
    use_container_width=True
)