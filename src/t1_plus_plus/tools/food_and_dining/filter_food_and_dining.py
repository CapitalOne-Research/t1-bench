import re

import pandas as pd

import t1_plus_plus.tools.food_and_dining.search_food_and_dining as sfad
from t1_plus_plus.schema.food_and_dining.filter_food_and_dining import FilterFoodAndDiningInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.tools.general.cache import get_results_from_cache


def filter_food_and_dining(**kwargs) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to apply additional filters to an existing list of food and dining search results based on criteria such as neighborhood, cuisine, rating, price level, and various venue features (like vegan options, free Wi-Fi, play area, etc.).

    Important:
        Before calling this tool, you MUST first call `get_results_from_cache` to retrieve the prior
        search results using the cache key from the previous search. Pass the cache key into the
        `cache_key` parameter of this tool.

    Examples:
    >>> # Usage Example: Filter by neighborhood
    filter_food_and_dining(cache_key="search_food_and_dining_results_0", neighborhood=["Downtown Austin"])

    >>> # Usage Example: Filter by rating range and neighborhood
    filter_food_and_dining(cache_key="search_food_and_dining_results_0", rating=[4.0, 5.0], neighborhood=["Wicker Park"])

    >>> # Usage Example: Filter on already-filtered results by dietary options
    filter_food_and_dining(cache_key="filter_food_and_dining_results_0", vegan_options=True, is_open=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting filtered establishments as well as the summary.
    """
    try:
        search_input = FilterFoodAndDiningInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    # Retrieve prior results from cache
    print(f"[filter_food_and_dining] Calling get_results_from_cache with key='{search_input.cache_key}'")
    prior_results = get_results_from_cache(key=search_input.cache_key)
    if prior_results is not None:
        _count = len(prior_results.search_results) if hasattr(prior_results, "search_results") else len(prior_results.get("search_results", []))
        print(f"[filter_food_and_dining] Cache returned {_count} item(s)")
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
        k: v
        for k, v in search_input.model_dump().items()
        if v is not None and k != "cache_key"
    }

    # Build prior summary (strip trailing count sentence)
    prior_summary = prior_results_dict.get("query_summary") or ""
    prior_summary = re.sub(
        r"There are.*?that matched this query!\.?$", "", prior_summary.strip()
    )

    summarized_query = sfad.summarize_query(search_input_filtered)
    complete_query = (
        f"{prior_summary}\nAdditionally filtering for {summarized_query}"
        if summarized_query
        else prior_summary
    )

    if not prior_search_results:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 establishment(s) that matched this query!",
        )

    # Hydrate: collect restaurant IDs from prior results, fetch full rows from master dataframe
    prior_ids = [
        item.get("restaurant_id") or item.get("id")
        for item in prior_search_results
        if isinstance(item, dict)
    ]
    prior_ids = [r for r in prior_ids if r]

    if sfad.all_food_and_dining_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    current_df = sfad.all_food_and_dining_df[sfad.all_food_and_dining_df["id"].isin(prior_ids)].copy()

    if current_df.empty:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 establishment(s) that matched this query!",
        )

    import numpy as np

    mask = pd.Series(True, index=current_df.index)

    for col, val in search_input_filtered.items():
        if col == "neighborhood":
            mask &= current_df["neighborhood"].isin(val)
        elif col == "cuisine":
            cuisine_masks = [
                current_df["cuisine"].str.lower().str.contains(c.lower(), na=False)
                for c in val
            ]
            mask &= np.logical_or.reduce(cuisine_masks)
        elif col == "restaurant_name":
            if "name" in current_df.columns:
                mask &= current_df["name"].isin(val)
        elif col == "restaurant_id":
            if "id" in current_df.columns:
                mask &= current_df["id"].isin(val)
        elif col == "price_per_person":
            mask &= current_df["price_per_person"] <= val
        elif col == "price_level":
            if "price_level" in current_df.columns:
                mask &= current_df["price_level"].isin(val)
        elif col == "rating":
            mask &= (current_df["rating"] >= val[0]) & (current_df["rating"] <= val[1])
        elif col.startswith("has_") or col.startswith("is_") or col.startswith("offers_") or col.startswith("supports_"):
            if col in current_df.columns:
                if current_df[col].dtype == object:
                    mask &= current_df[col].astype(str).str.lower() == str(val).lower()
                else:
                    mask &= current_df[col] == val
        elif col in current_df.columns:
            mask &= current_df[col] == val

    resulting_restaurants = current_df[mask]

    if len(resulting_restaurants) == 0:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 establishment(s) that matched this query!",
        )

    extracted_results = [
        {
            "restaurant_id": row.get("id"),
            "name": row.get("name"),
            "city": row.get("city"),
            "state": row.get("state"),
            "neighborhood": row.get("neighborhood"),
            "cuisine": row.get("cuisine"),
            "price_per_person": row.get("price_per_person"),
            "price_level": row.get("price_level"),
            "rating": row.get("rating"),
        }
        for row in resulting_restaurants.head(10).to_dict(orient="records")
    ]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{complete_query}\nThere are {len(extracted_results)} establishment(s) that matched this query!",
    )
