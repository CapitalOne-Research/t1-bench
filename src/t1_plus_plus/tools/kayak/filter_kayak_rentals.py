import re
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from t1_plus_plus.schema.kayak.filter_kayak_rentals import FilterKayakRentalsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.schema.kayak.kayak_rental_item import KayakRentalItem
from t1_plus_plus.tools.general.cache import get_results_from_cache

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


def filter_kayak_rentals(**kwargs: Any) -> SearchResultsOutputModel:
    """
    Takes prior search results (loaded from cache) and applies additional filters to narrow them down.
    """
    try:
        filter_input = FilterKayakRentalsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Error: Input validation error: {str(e)}"
        )

    # Retrieve prior results from cache
    prior_results = get_results_from_cache(key=filter_input.cache_key)
    if prior_results is None:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"Error: No cached results found for key '{filter_input.cache_key}'.",
        )

    if hasattr(prior_results, "model_dump"):
        prior_results_dict = prior_results.model_dump()
    else:
        prior_results_dict = prior_results

    prior_rentals = prior_results_dict.get("search_results", [])

    filter_input_dict = {
        k: v for k, v in filter_input.model_dump().items() if v is not None and k != "cache_key"
    }

    # Build prior summary (strip trailing count sentence)
    prior_message = prior_results_dict.get("query_summary") or ""
    prior_message = re.sub(
        r"There are.*?that matched this query!\.?$", "", prior_message.strip()
    )

    # Summarize the NEW filter parameters
    summarized_new_query = summarize_kayak_query(filter_input_dict)
    complete_query = (
        f"{prior_message}\nAdditionally filtering for: {summarized_new_query}"
        if summarized_new_query
        else prior_message
    )

    if not prior_rentals:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 rental(s) that matched this query!",
        )

    # Hydrate IDs from previous results
    prior_ids = [
        item.get("rental_id") for item in prior_rentals if item.get("rental_id")
    ]

    if all_kayak_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Error: Database is currently unavailable."
        )

    # Filter the global DataFrame using ONLY the prior IDs
    current_df = all_kayak_df[all_kayak_df["rental_id"].isin(prior_ids)]
    mask = pd.Series(True, index=current_df.index)

    # Apply the new filters
    for col, params in filter_input_dict.items():
        if col == "neighborhood":
            mask &= current_df["neighborhood"].isin(params)
        elif col == "vessel_type":
            mask &= current_df["vessel_type"].isin(params)
        elif col == "business_name":
            mask &= current_df["business_name"].isin(params)
        elif col == "rating":
            mask &= (current_df["rating"] >= params[0]) & (current_df["rating"] <= params[1])
        elif col == "price_per_hour":
            mask &= (current_df["price_per_hour"] >= params[0]) & (current_df["price_per_hour"] <= params[1])

    resulting_rentals = current_df[mask].to_dict(orient="records")

    if len(resulting_rentals) == 0:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 rental(s) that matched this query!",
        )

    top_10 = resulting_rentals[:10]
    extracted_results = [KayakRentalItem(**item).model_dump() for item in top_10]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{complete_query}\nThere are {len(extracted_results)} rental(s) that matched this query!",
    )
