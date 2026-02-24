# etl/load.py
import os
import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def save_raw(raw_works: list, filename: str = "works_raw.parquet"):
    ensure_dirs()
    df = pd.DataFrame(raw_works)
    path = RAW_DIR / filename
    df.to_parquet(path, index=False)
    print(f"[load] Saved {len(df)} raw works to {path}")
    return path

def save_processed(df: pd.DataFrame, filename: str):
    ensure_dirs()
    path = PROCESSED_DIR / filename
    df.to_parquet(path, index=False)
    print(f"[load] Saved {len(df)} rows to {path}")
    return path

def load_processed(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run etl/refresh.py first to build the data cache."
        )
    return pd.read_parquet(path)

def load_all():
    """
    Convenience loader for the dashboard. Returns all processed tables
    optimized with categorical data types for maximum filtering speed.
    """
    works = load_processed("works.parquet")
    country_edges = load_processed("country_edges.parquet")
    institution_edges = load_processed("institution_edges.parquet")
    
    # --- Convert heavy text columns to categories ---
    
    # Optimize Works table
    if "type" in works.columns:
        works["type"] = works["type"].astype("category")
    if "oa_status" in works.columns:
        works["oa_status"] = works["oa_status"].astype("category")
        
    # Optimize Country Edges
    if "country_code" in country_edges.columns:
        country_edges["country_code"] = country_edges["country_code"].astype("category")
        
    # Optimize Institution Edges
    if "target" in institution_edges.columns:
        institution_edges["target"] = institution_edges["target"].astype("category")
    if "target_country" in institution_edges.columns:
        institution_edges["target_country"] = institution_edges["target_country"].astype("category")
    if "source" in institution_edges.columns:
        institution_edges["source"] = institution_edges["source"].astype("category")

    return works, country_edges, institution_edges