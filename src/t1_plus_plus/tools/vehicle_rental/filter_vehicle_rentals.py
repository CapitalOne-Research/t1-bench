import re

import pandas as pd

import t1_plus_plus.tools.vehicle_rental.search_vehicle_rentals as sr
from t1_plus_plus.schema.vehicle_rental.filter_vehicle_rentals import FilterRentalsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.tools.general.cache import get_results_from_cache


def filter_vehicle_rentals(**kwargs) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to apply additional filters to an existing list of rental vehicles based on
        criteria such as make, model, year, category, price tier, and various features
        (like GPS, automatic transmission, pet-friendly, etc.).

    Important:
        Before calling this tool, you MUST first call `search_vehicle_rentals` so results are stored in the cache.
        Pass the cache key into the `cache_key` parameter — do NOT use `prior_results`.
        Cache key values:
          - 'search_vehicle_rentals_results_0' — results from the first (or only) search_vehicle_rentals call
          - 'search_vehicle_rentals_results_1' — results from a second search_vehicle_rentals call (compare scenario)

    Examples:
    >>> # Usage Example:
    filter_vehicle_rentals(cache_key="search_vehicle_rentals_results_0", category="car", is_automatic=True)

    >>> # Usage Example:
    filter_vehicle_rentals(cache_key="search_vehicle_rentals_results_0", base_price_per_day=75.0, is_pet_friendly=True, has_gps=True)

    >>> # Usage Example:
    filter_vehicle_rentals(cache_key="search_vehicle_rentals_results_0", rating=[4.0, 5.0], fuel_type="electric", has_unlimited_mileage=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting filtered rental vehicles as well as the summary.
    """
    try:
        search_input = FilterRentalsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    # Retrieve prior results from cache
    print(
        f"[filter_vehicle_rentals] Calling get_results_from_cache with key='{search_input.cache_key}'"
    )
    prior_results = get_results_from_cache(key=search_input.cache_key)
    if prior_results is not None:
        _count = (
            len(prior_results.search_results)
            if hasattr(prior_results, "search_results")
            else len(prior_results.get("search_results", []))
        )
        print(f"[filter_vehicle_rentals] ✅ [CACHE LOADED] Cache returned {_count} item(s)")
    if prior_results is None:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"Error: No cached results found for key '{search_input.cache_key}'.",
        )

    if hasattr(prior_results, "model_dump"):
        prior_results_dict = prior_results.model_dump()
    else:
        prior_results_dict = prior_results

    prior_search_results = prior_results_dict.get("search_results", [])

    search_input_filtered = {
        k: v for k, v in search_input.model_dump().items() if v is not None and k != "cache_key"
    }

    # Build prior summary (strip trailing count sentence)
    prior_summary = prior_results_dict.get("query_summary") or ""
    prior_summary = re.sub(
        r"There are.*?that matched this query!\.?$", "", prior_summary.strip()
    )

    summarized_query = sr.summarize_rental_query(search_input_filtered)
    complete_query = (
        f"{prior_summary}\nAdditionally filtering for {summarized_query}"
        if summarized_query
        else prior_summary
    )

    if not prior_search_results:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 vehicle(s) that matched this query!",
        )

    # Hydrate IDs from cache results against the master DataFrame
    prior_ids = []
    for item in prior_search_results:
        if isinstance(item, dict):
            rid = item.get("vehicle_id") or item.get("id")
            if rid:
                prior_ids.append(rid)

    if sr.all_rentals_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    current_df = sr.all_rentals_df[sr.all_rentals_df["id"].isin(prior_ids)]
    mask = pd.Series(True, index=current_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "make":
            mask &= current_df["make"].isin(search_query_parameters)

        elif col == "model":
            mask &= current_df["model"].isin(search_query_parameters)

        elif col == "year":
            mask &= current_df["year"].isin(search_query_parameters)

        elif col == "category":
            mask &= current_df["category"] == search_query_parameters

        elif col == "price_tier":
            mask &= current_df["price_tier"] == search_query_parameters

        elif col == "base_price_per_day":
            mask &= current_df["base_price_per_day"] <= search_query_parameters

        elif col == "odometer":
            mask &= current_df["odometer"] <= search_query_parameters

        elif col == "seats":
            mask &= current_df["seats"] >= search_query_parameters

        elif col == "fuel_type":
            mask &= current_df["fuel_type"] == search_query_parameters

        elif col == "rating":
            mask &= (current_df["rating"] >= search_query_parameters[0]) & (
                current_df["rating"] <= search_query_parameters[1]
            )

        elif col == "vehicle_id":
            if "id" in current_df.columns:
                mask &= current_df["id"].isin(search_query_parameters)

        elif col.startswith("has_") or col.startswith("is_"):
            if col in current_df.columns:
                if current_df[col].dtype == object:
                    mask &= (
                        current_df[col].astype(str).str.lower()
                        == str(search_query_parameters).lower()
                    )
                else:
                    mask &= current_df[col] == search_query_parameters

    resulting_rentals = (current_df[mask]).to_dict(orient="records")

    if len(resulting_rentals) == 0:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 vehicle(s) that matched this query!",
        )

    extracted_results = [
        {
            "vehicle_id": item.get("id"),
            "make": item.get("make"),
            "model": item.get("model"),
            "year": item.get("year"),
            "city": item.get("city"),
            "category": item.get("category"),
            "price_tier": item.get("price_tier"),
            "base_price_per_day": item.get("base_price_per_day"),
            "rating": item.get("rating"),
        }
        for item in resulting_rentals[:10]
    ]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{complete_query}\nThere are {len(extracted_results)} vehicle(s) that matched this query!",
    )
