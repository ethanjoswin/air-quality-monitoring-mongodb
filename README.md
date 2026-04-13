# Air Quality Monitoring and Analytics System

## Overview
This project is about collecting air pollution data and showing it in a dashboard.  
It uses public APIs to get live and historical data, stores everything in MongoDB, and then displays trends, weather info, and alerts using Streamlit.

## What it does
- Collects live air quality data
- Loads historical pollution data
- Stores data in MongoDB
- Cleans missing or incomplete data
- Shows results in a dashboard
- Displays alerts for high pollution
- Allows downloading data as CSV

## Tools used
- Python
- MongoDB
- Pandas
- Requests
- Streamlit

## Project structure
- `scripts/` → backend (data collection and processing)
- `frontend/` → dashboard
- `tests/` → test files

## How to run

Install dependencies:
```bash
pip install -r requirements.txt