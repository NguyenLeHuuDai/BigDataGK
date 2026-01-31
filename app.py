import streamlit as st
from pymongo import MongoClient
import pandas as pd
import vaex

@st.cache_data
def load_data():
    uri = (
        "mongodb+srv://dainlh21405:qqOjroljGq2s18Qc@cluster0.catt6oh.mongodb.net/"
        "mydb?retryWrites=true&w=majority&tls=true")
    client = MongoClient(uri)
    collection = client["mydb"]["mycollection"]

    df_pd = pd.DataFrame(list(collection.find({}, {"_id": 0})))

    df_pd["year"] = df_pd["title"].str.extract(r"\((\d{4})\)").astype("Int64")
    df_pd["year"] = pd.to_numeric(df_pd["year"], errors="coerce")
    df_pd["clean_title"] = df_pd["title"].str.replace(r"\s*\(\d{4}\)", "", regex=True)
    df_pd["genres_list"] = df_pd["genres"].str.split("|")

    return vaex.from_pandas(df_pd)

# ===== UI =====
st.title("🎬 Movie Data Analysis")

df = load_data()

st.subheader("Raw data")
st.dataframe(
    df.head(100)
      .to_pandas_df()[["movieId", "clean_title", "year", "genres_list"]]
)
# ===== Filter by year =====
year_range = st.slider(
    "Select year range",
    int(df.year.min()),
    int(df.year.max()),
    (2000, 2010)
)

df_filtered = df[(df.year >= year_range[0]) & (df.year <= year_range[1])]

# ===== Movies per year =====
movies_per_year = df_filtered.groupby(
    "year", agg={"count": vaex.agg.count()}
)

st.subheader("Movies per year")
st.line_chart(movies_per_year.to_pandas_df().set_index("year"))

# ===== Genre analysis =====
df_pd = df_filtered.to_pandas_df()
df_genre = df_pd.explode("genres_list")

genre_count = (
    df_genre
    .groupby("genres_list")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

st.subheader("Top genres")
st.bar_chart(
    genre_count
    .set_index("genres_list")
    .head(10)
)
# ===== Xu hướng thể loại=====
genre_year = (
    df_genre
    .groupby(["year", "genres_list"])
    .size()
    .reset_index(name="count")
)

pivot = genre_year.pivot(
    index="year",
    columns="genres_list",
    values="count"
).fillna(0)

st.subheader("📈 Xu hướng thể loại theo thời gian")
st.area_chart(pivot)

# ===== Năm đột biến=====
year_count = (
    df_filtered
    .groupby("year", agg={"count": vaex.agg.count()})
    .to_pandas_df()
    .sort_values("year")
)

q1 = year_count["count"].quantile(0.25)
q3 = year_count["count"].quantile(0.75)
iqr = q3 - q1

outliers = year_count[
    (year_count["count"] < q1 - 1.5 * iqr) |
    (year_count["count"] > q3 + 1.5 * iqr)
]

st.subheader("⚠️ Anomalous years")
st.dataframe(outliers)
