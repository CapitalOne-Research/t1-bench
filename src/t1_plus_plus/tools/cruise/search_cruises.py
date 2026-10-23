import os
import pandas as pd
from pathlib import Path
from t1_plus_plus.schema.cruise.search_cruises import SearchCruisesInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
CSV_PATH = os.getenv("ALL_CRUISES", str(_data_dir / "data_cruises.csv"))
all_cruises_df = pd.read_csv(CSV_PATH) if Path(CSV_PATH).exists() else pd.DataFrame()

def summarize_cruise_query(search_input_filtered):
    result = []
    if "destination" in search_input_filtered:
        result.append(f"Cruise search results for destination '{search_input_filtered['destination']}',")
    if "departure_port" in search_input_filtered:
        result.append(f"departing from {search_input_filtered['departure_port']},")
    if "cruise_line" in search_input_filtered:
        lines = ", ".join(search_input_filtered["cruise_line"])
        result.append(f"on lines [{lines}],")
    if "duration_nights" in search_input_filtered:
        durations = ", ".join(map(str, search_input_filtered["duration_nights"]))
        result.append(f"for duration(s) [{durations}] nights,")
    if "tier" in search_input_filtered:
        result.append(f"for tier {search_input_filtered['tier']},")
    if "rating" in search_input_filtered:
        r = search_input_filtered["rating"]
        result.append(f"rating between {r[0]} and {r[1]},")

    cabin = search_input_filtered.get("cabin_type", "interior").replace("_", " ")
    if "price_per_person_max" in search_input_filtered:
        result.append(f"max budget ${search_input_filtered['price_per_person_max']} per person for {cabin} cabin,")

    features = [k for k, v in search_input_filtered.items() if (k.startswith("has_") or k.startswith("is_") or k.endswith("_included")) and v is True]
    if features:
        feature_names = ", ".join([f.replace("has_", "").replace("is_", "").replace("_", " ") for f in features])
        result.append(f"with features: [{feature_names}],")

    final_result = " ".join(result)
    return final_result.rstrip(",") + "."

def search_cruises(**kwargs: SearchCruisesInputModel) -> SearchResultsOutputModel:
    try:
        search_input = SearchCruisesInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    search_input_filtered = {k: v for k, v in search_input.model_dump().items() if v is not None}

    if all_cruises_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    mask = pd.Series(True, index=all_cruises_df.index)

    for col, val in search_input_filtered.items():
        if col == "destination":
            mask &= all_cruises_df["destination"].str.contains(val, case=False, na=False)
        elif col == "departure_port":
            mask &= all_cruises_df["departure_port"].str.lower() == val.lower()
        elif col == "cruise_line":
            mask &= all_cruises_df["cruise_line"].isin(val)
        elif col == "duration_nights":
            mask &= all_cruises_df["duration_nights"].isin(val)
        elif col == "tier":
            mask &= all_cruises_df["tier"] == val
        elif col == "rating":
            mask &= (all_cruises_df["rating"] >= val[0]) & (all_cruises_df["rating"] <= val[1])
        elif col == "price_per_person_max":
            cabin_raw = search_input_filtered.get("cabin_type", "interior")
            price_col = f"{cabin_raw}_price_per_person"
            if price_col in all_cruises_df.columns:
                mask &= all_cruises_df[price_col] <= val
        elif col == "cabin_type":
            avail_col = f"{val}_available"
            if avail_col in all_cruises_df.columns:
                mask &= all_cruises_df[avail_col] > 0
        elif col.startswith("has_") or col.startswith("is_") or col.endswith("_included"):
            if col in all_cruises_df.columns:
                mask &= all_cruises_df[col] == val

    resulting_cruises = all_cruises_df[mask].to_dict(orient="records")
    summarized_query = summarize_cruise_query(search_input_filtered)

    if len(resulting_cruises) == 0:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{summarized_query}\nThere are 0 cruise(s) that matched this query!"
        )

    top_10 = resulting_cruises[:10]

    # FIX: Properly fetch 'cruise_id' since that's what the dataset uses
    extracted_results = [
        {
            "cruise_id": item.get("cruise_id"),
            "destination": item.get("destination"),
            "departure_port": item.get("departure_port"),
            "cruise_line": item.get("cruise_line"),
            "duration_nights": item.get("duration_nights"),
            "tier": item.get("tier"),
            "rating": item.get("rating")
        }
        for item in top_10
    ]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{summarized_query}\nThere are {len(extracted_results)} cruise(s) that matched this query!"
    )
