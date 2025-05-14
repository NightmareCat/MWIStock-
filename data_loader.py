import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import urllib.request

DB_URL = "https://raw.githubusercontent.com/holychikenz/MWIApi/main/market.db"
DB_PATH = "cache/market.db"


def get_price_data(item_name: str, n_days: int = 7) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    cutoff = int((datetime.utcnow() - timedelta(days=n_days)).timestamp())
    
    ask_query = f"SELECT time, [{item_name}] as ask FROM ask WHERE time >= {cutoff}"
    bid_query = f"SELECT time, [{item_name}] as bid FROM bid WHERE time >= {cutoff}"

    ask_df = pd.read_sql_query(ask_query, conn)
    bid_df = pd.read_sql_query(bid_query, conn)
    conn.close()

    merged = pd.merge(ask_df, bid_df, on="time", how="outer").sort_values("time")
    merged["datetime"] = pd.to_datetime(merged["time"], unit="s")
    return merged

def download_db_if_needed():
    os.makedirs("cache", exist_ok=True)
    if not os.path.exists(DB_PATH):
        print("Downloading market.db...")
        urllib.request.urlretrieve(DB_URL, DB_PATH)
        print("Download complete.")