import pandas as pd


def get_aqi_category(aqi):
    mapping = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor"
    }
    return mapping.get(aqi, "Unknown")


def to_dublin_hour(unix_timestamp):
    return (
        pd.to_datetime(unix_timestamp, unit="s", utc=True)
        .tz_convert("Europe/Dublin")
        .tz_localize(None)
        .floor("h")
        .to_pydatetime()
    )