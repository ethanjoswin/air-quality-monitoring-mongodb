import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient


env_candidates = [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]

for env_path in env_candidates:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env file")

client = MongoClient(MONGO_URI)
db = client["air_quality_db"]
pollution_collection = db["pollution_data"]
alerts_collection = db["alerts"]

st.set_page_config(page_title="Air Quality Dashboard", layout="wide")


def get_health_advice(aqi):
    if aqi is None or pd.isna(aqi):
        return "No AQI advice available yet."
    if aqi == 1:
        return "Air quality is good. Outdoor activity is fine."
    if aqi == 2:
        return "Air quality is fair. Normal activity is usually okay."
    if aqi == 3:
        return "Air quality is moderate. Sensitive people should reduce long outdoor exposure."
    if aqi == 4:
        return "Air quality is poor. Reduce outdoor activity and consider wearing a mask."
    if aqi >= 5:
        return "Air quality is very poor. Avoid outdoor activity when possible."
    return "AQI value is outside expected range."


def load_pollution_df():
    pollution_docs = list(
        pollution_collection.find(
            {},
            {
                "_id": 0,
                "datetime": 1,
                "pm2_5": 1,
                "pm10": 1,
                "no2": 1,
                "o3": 1,
                "co": 1,
                "aqi": 1,
                "aqi_category": 1,
                "temperature": 1,
                "humidity": 1,
                "pressure": 1,
                "wind_speed": 1,
                "source": 1,
            },
        ).sort("datetime", 1)
    )

    df = pd.DataFrame(pollution_docs)
    if df.empty:
        return df

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"])
    df = df.sort_values("datetime").drop_duplicates(subset=["datetime"]).reset_index(drop=True)

    numeric_cols = [
        "pm2_5", "pm10", "no2", "o3", "co", "aqi",
        "temperature", "humidity", "pressure", "wind_speed"
    ]

    for col in numeric_cols:
        if col not in df.columns:
            df[col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df[numeric_cols] = df[numeric_cols].interpolate(limit_direction="both").ffill().bfill()
    df["day_name"] = df["datetime"].dt.day_name()
    df["hour"] = df["datetime"].dt.hour
    df["date"] = df["datetime"].dt.date
    return df


def daily_summary(df):
    return (
        df.groupby("date", as_index=False)[["pm2_5", "pm10", "no2", "o3", "aqi"]]
        .mean()
        .sort_values("date")
    )


def safe_value(value, decimals=2):
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}"


st.title("Air Quality Monitoring and Analytics Dashboard")
st.write("Live air pollution, weather insights, weekly analysis, and alerts for Dublin")

alert_docs = list(alerts_collection.find({}, {"_id": 0}).sort("datetime", -1).limit(20))
df = load_pollution_df()

if df.empty:
    st.error("No pollution data found in MongoDB.")
    st.stop()

min_date = df["datetime"].min().date()
max_date = df["datetime"].max().date()

st.sidebar.header("Filters")
selected_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
pollutant = st.sidebar.selectbox(
    "Select pollutant",
    ["pm2_5", "pm10", "no2", "o3", "co", "aqi"]
)

if isinstance(selected_range, tuple) and len(selected_range) == 2:
    start_date, end_date = selected_range
else:
    start_date = end_date = selected_range

filtered_df = df[
    (df["datetime"].dt.date >= start_date) &
    (df["datetime"].dt.date <= end_date)
].copy()

if filtered_df.empty:
    st.warning("No data for selected date range.")
    st.stop()

latest = filtered_df.iloc[-1]

st.subheader("Latest Air Quality Status")
col1, col2, col3, col4 = st.columns(4)
col1.metric("PM2.5", safe_value(latest["pm2_5"]))
col2.metric("PM10", safe_value(latest["pm10"]))
col3.metric("AQI", safe_value(latest["aqi"], 0))
col4.metric("AQI Category", latest.get("aqi_category", "N/A"))

st.info(get_health_advice(latest.get("aqi")))
st.write("Latest record time:", latest["datetime"])

st.subheader("Current Weather Conditions")
w1, w2, w3, w4 = st.columns(4)
w1.metric("Temperature (°C)", safe_value(latest["temperature"]))
w2.metric("Humidity (%)", safe_value(latest["humidity"]))
w3.metric("Pressure", safe_value(latest["pressure"]))
w4.metric("Wind Speed", safe_value(latest["wind_speed"]))

st.subheader("Trend Analysis")
trend_df = filtered_df[["datetime", pollutant]].set_index("datetime")
st.line_chart(trend_df)

st.subheader("Daily Average Pollution")
daily_df = daily_summary(filtered_df).set_index("date")
st.bar_chart(daily_df[["pm2_5", "pm10"]])

st.subheader("Hourly Pollution Pattern")
hourly_pattern = filtered_df.groupby("hour")[["pm2_5", "pm10", "no2", "o3"]].mean()
st.line_chart(hourly_pattern)

st.subheader("Which Day Has More Pollution?")
weekly_pollution = (
    filtered_df.groupby("day_name")["pm2_5"]
    .mean()
    .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    .dropna()
)

if not weekly_pollution.empty:
    worst_day = weekly_pollution.idxmax()
    worst_value = weekly_pollution.max()
    st.success(f"Highest average PM2.5 is on {worst_day}: {worst_value:.2f}")
    st.bar_chart(weekly_pollution)
else:
    st.info("Not enough weekly data yet.")

st.subheader("Peak Pollution Record")
peak_row = filtered_df.loc[filtered_df["pm2_5"].idxmax()]
st.write(f"Peak PM2.5 in selected range: {peak_row['pm2_5']:.2f} at {peak_row['datetime']}")

st.subheader("Pollution Heatmap Table")
heatmap_df = filtered_df.pivot_table(values="pm2_5", index="day_name", columns="hour", aggfunc="mean")
heatmap_df = heatmap_df.reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
st.dataframe(heatmap_df, use_container_width=True)

st.subheader("Recent Alerts")
if alert_docs:
    alert_df = pd.DataFrame(alert_docs)
    if "datetime" in alert_df.columns:
        alert_df["datetime"] = pd.to_datetime(alert_df["datetime"])
    st.dataframe(alert_df, use_container_width=True)
else:
    st.info("No alerts found.")

st.subheader("Download Filtered Data")
csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download filtered data as CSV",
    data=csv_data,
    file_name="filtered_air_quality_data.csv",
    mime="text/csv"
)

with st.expander("Show Raw Pollution Data"):
    st.dataframe(filtered_df.tail(100), use_container_width=True)