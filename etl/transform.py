import pandas as pd

def extract_concepts(concepts, top_n=5):
    # Safely catch None, Pandas NaN (float), or empty arrays/lists
    if concepts is None or isinstance(concepts, float) or len(concepts) == 0:
        return []
    
    # Sort safely, ensuring we are dealing with dictionaries
    sorted_concepts = sorted(
        concepts, 
        key=lambda x: x.get("score", 0) if isinstance(x, dict) else 0, 
        reverse=True
    )
    
    top_concepts = []
    for c in sorted_concepts[:top_n]:
        if isinstance(c, dict):
            top_concepts.append({
                "name": c.get("display_name"),
                "level": c.get("level"),
                "score": c.get("score")
            })
            
    return top_concepts

def extract_countries(authorships, exclude_institution_id="I185261750"):
    countries = []
    if authorships is None or isinstance(authorships, float) or len(authorships) == 0:
        return countries
        
    for authorship in authorships:
        if not isinstance(authorship, dict): 
            continue
        for inst in authorship.get("institutions", []):
            if not isinstance(inst, dict): 
                continue
                
            inst_id = inst.get("id") or ""  
            if inst_id.split("/")[-1] != exclude_institution_id:
                country = inst.get("country_code")
                if country:
                    countries.append(country)
    return list(set(countries))

def extract_institutions(authorships, exclude_id="I185261750"):
    institutions = []
    if authorships is None or isinstance(authorships, float) or len(authorships) == 0:
        return institutions
        
    for authorship in authorships:
        if not isinstance(authorship, dict): 
            continue
        for inst in authorship.get("institutions", []):
            if not isinstance(inst, dict): 
                continue
                
            inst_id = inst.get("id") or ""
            if inst_id.split("/")[-1] != exclude_id:
                institutions.append({
                    "name": inst.get("display_name"),
                    "country": inst.get("country_code"),
                    "ror": inst.get("ror"),
                    "openalex_id": inst.get("id")
                })
    return institutions

def transform_works(raw_works):
    """Flatten raw OpenAlex works into a tidy DataFrame."""
    rows = []
    for w in raw_works:
        # Get the list of top 5 concepts
        top_concepts_list = extract_concepts(w.get("concepts", []), top_n=5)
        
        primary_concept = top_concepts_list[0]["name"] if top_concepts_list else None
        primary_concept_level = top_concepts_list[0]["level"] if top_concepts_list else None
        
        collab_countries = extract_countries(w.get("authorships", []))
        collab_institutions = extract_institutions(w.get("authorships", []))
        
        # Safely navigate the nested dictionaries. 
        # If 'primary_location' or 'source' are explicitly None, 'or {}' catches it.
        primary_loc = w.get("primary_location") or {}
        source_dict = primary_loc.get("source") or {}
        source_name = source_dict.get("display_name")
        # ---------------
        
        rows.append({
            "id": w.get("id"),
            "title": w.get("title"),
            "year": w.get("publication_year"),
            "type": w.get("type"),
            "is_oa": w.get("open_access", {}).get("is_oa"),
            "oa_status": w.get("open_access", {}).get("oa_status"),
            "cited_by_count": w.get("cited_by_count", 0),
            "top_concept": primary_concept,
            "concept_level": primary_concept_level,
            "all_top_concepts": top_concepts_list, 
            "collab_countries": collab_countries,      
            "collab_institutions": collab_institutions, 
            "author_count": len(w.get("authorships", [])),
            "source_name": source_name,
        })
    
    return pd.DataFrame(rows)

def build_country_edges(df):
    """
    Creates a long-format DataFrame for the choropleth map.
    Now includes granular concept data for advanced filtering.
    """
    rows = []
    for _, row in df.iterrows():
        for country in row["collab_countries"]:
            rows.append({
                "work_id": row["id"],
                "year": row["year"],
                "country_code": country,
                "top_concept": row["top_concept"],
                "all_top_concepts": row["all_top_concepts"] # Added this
            })
    return pd.DataFrame(rows)

def build_institution_edges(df):
    """
    Creates edges for network graph: UofT -> collaborating institution.
    Now includes concept data so the network can be filtered by topic.
    """
    rows = []
    for _, row in df.iterrows():
        for inst in row["collab_institutions"]:
            rows.append({
                "source": "University of Toronto",
                "target": inst["name"],
                "target_country": inst["country"],
                "year": row["year"],
                "work_id": row["id"],
                "top_concept": row["top_concept"],          # Added this
                "all_top_concepts": row["all_top_concepts"] # Added this
            })
    return pd.DataFrame(rows)