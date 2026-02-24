import pyalex
from pyalex import Works
import pandas as pd
from tqdm import tqdm
import os
from dotenv import load_dotenv

pyalex.config.email = os.getenv("OPENALEX_EMAIL") # polite pool

UOFT_ID = "I185261750"

def fetch_works(start_year=2020, end_year=2026, per_page=200):
    """
    Fetch all works with at least one UofT author.
    Returns a list of raw work dicts.
    """
    all_works = []
    
    pager = (
        Works()
        .filter(
            authorships={"institutions": {"id": UOFT_ID}},
            publication_year=f"{start_year}-{end_year}"
        )
        .select([
            "id", "title", "publication_year", "publication_date",
            "type", "open_access", "cited_by_count", "concepts",
            "authorships", "primary_location", "locations",
            "referenced_works_count", "counts_by_year"
        ])
        .paginate(per_page=per_page, n_max=None)  # n_max=None = fetch all
    )
    
    for page in tqdm(pager, desc="Fetching works"):
        all_works.extend(page)
    
    return all_works