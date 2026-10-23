import uuid
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from t1_plus_plus.schema.kayak.search_kayak_rentals import SearchKayakRentalsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.schema.kayak.kayak_rental_item import KayakRentalItem

# Load the CSV — resolve relative to this file so it works regardless of cwd or import path
_data_dir = Path(__file__).resolve().parents[4] / "datasets"
_CSV_PATH = str(_data_dir / "data_kayak_rental.csv")
try:
    all_kayak_df = pd.read_csv(_CSV_PATH)
except FileNotFoundError:
    all_kayak_df = pd.DataFrame()


def summarize_kayak_query(search_input_filtered: Dict[str, Any]) -> str:
    """Creates a human-readable summary of the search query parameters."""
    result = []

    if "city" in search_input_filtered:
        result.append(f"Kayak search results in {search_input_filtered['city']},")
    if "state" in search_input_filtered:
        result.append(f"state of {search_input_filtered['state']},")
    if "neighborhood" in search_input_filtered:
        neighborhoods = ", ".join(search_input_filtered["neighborhood"])
        result.append(f"in neighborhood(s) [{neighborhoods}],")
    if "business_name" in search_input_filtered:
        names = ", ".join(search_input_filtered["business_name"])
        result.append(f"for business(es) [{names}],")
    if "vessel_type" in search_input_filtered:
        vessels = ", ".join(search_input_filtered["vessel_type"])
        result.append(f"for vessel type(s) [{vessels}],")
    if "rating" in search_input_filtered:
        rating = search_input_filtered["rating"]
        result.append(f"rating between {rating[0]} and {rating[1]},")
    if "price_per_hour" in search_input_filtered:
        price = search_input_filtered["price_per_hour"]
        result.append(f"hourly price between ${price[0]} and ${price[1]},")

    final_result = " ".join(result).strip()
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."
    elif not final_result:
        final_result = "Showing all available kayak rentals."

    return final_result


def search_kayak_rentals(**kwargs: Any) -> SearchResultsOutputModel:
    """
    Search for kayak rentals based on criteria like city, neighborhood, vessel_type, etc.
    """
    try:
        search_input = SearchKayakRentalsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"Error: Input validation error: {str(e)}",
        )

    # Filter out None values
    search_input_filtered = {
        k: v for k, v in search_input.model_dump().items() if v is not None
    }

    if all_kayak_df.empty:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary="Error: Database is currently unavailable.",
        )

    mask = pd.Series(True, index=all_kayak_df.index)

    # Iterate through parameters and apply filters (ignoring parameters not tracked in DataFrame)
    for col, params in search_input_filtered.items():
        if col not in all_kayak_df.columns and col not in ["rating", "price_per_hour"]:
            continue  # Ignore extra fields not in DB

        if col == "city":
            mask &= all_kayak_df["city"].str.lower() == params.lower()
        elif col == "state":
            mask &= all_kayak_df["state"].str.lower() == params.lower()
        elif col == "neighborhood":
            mask &= all_kayak_df["neighborhood"].isin(params)
        elif col == "vessel_type":
            mask &= all_kayak_df["vessel_type"].isin(params)
        elif col == "business_name":
            mask &= all_kayak_df["business_name"].isin(params)
        elif col == "rating":
            mask &= (all_kayak_df["rating"] >= params[0]) & (all_kayak_df["rating"] <= params[1])
        elif col == "price_per_hour":
            mask &= (all_kayak_df["price_per_hour"] >= params[0]) & (all_kayak_df["price_per_hour"] <= params[1])

    resulting_rentals = all_kayak_df[mask].to_dict(orient="records")
    summarized_query = summarize_kayak_query(search_input_filtered)

    if len(resulting_rentals) == 0:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{summarized_query}\nThere are 0 rentals that matched this query!",
        )

    # Limit to top 10 results to prevent context bloat
    top_10 = resulting_rentals[:10]

    # Cast correctly into the KayakRentalItem schema, then convert to dicts
    extracted_results = [KayakRentalItem(**item).model_dump() for item in top_10]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{summarized_query}\nThere are {len(extracted_results)} rental(s) that matched this query!",
    )
