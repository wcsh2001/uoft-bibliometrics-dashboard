# recover.py
import pandas as pd
from etl.transform import transform_works, build_country_edges, build_institution_edges
from etl.load import save_processed

def run_recovery():
    print("Loading raw data from disk... (skipping API fetch)")
    
    # Load the parquet file we saved right before the crash
    raw_df = pd.read_parquet("data/raw/works_raw.parquet")
    
    # Convert it back to a list of dictionaries for the transform functions
    raw_works = raw_df.to_dict(orient="records")
    
    print("Transforming data...")
    df = transform_works(raw_works)
    country_df = build_country_edges(df)
    inst_df = build_institution_edges(df)
    
    print("Saving processed data...")
    save_processed(df, "works.parquet")
    save_processed(country_df, "country_edges.parquet")
    save_processed(inst_df, "institution_edges.parquet")
    print("Recovery complete! The dashboard is ready.")

if __name__ == "__main__":
    run_recovery()