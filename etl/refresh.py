# etl/refresh.py
from etl.extract import fetch_works
from etl.transform import transform_works, build_country_edges, build_institution_edges
from etl.load import save_processed, save_raw # Imported save_raw

def full_refresh():
    print("Starting data refresh...")
    raw = fetch_works(start_year=2020)
    
    # --- THE FIX ---
    # Save the raw data immediately. If the transform fails, the data is safe on disk!
    save_raw(raw, "works_raw.parquet") 
    print("Extract complete. Transforming data...")
    # ---------------
    
    df = transform_works(raw)
    country_df = build_country_edges(df)
    inst_df = build_institution_edges(df)
    
    save_processed(df, "works.parquet")
    save_processed(country_df, "country_edges.parquet")
    save_processed(inst_df, "institution_edges.parquet")
    
    print(f"Refresh complete. {len(df)} works saved.")

if __name__ == "__main__":      
    full_refresh()