from typing import Any

import pandas as pd

from t1_plus_plus.schema.attraction.attraction import (
    Attraction,
    FilterAttractionsInputModel,
)
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.tools.general.cache import get_results_from_cache


def filter_attractions(**kwargs: Any) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to apply additional filters to an existing list of attractions based on criteria such as city, state, attraction type, and rating.

    Examples:
    >>> # Usage Example:
    filter_attractions(cache_key="search_attractions_results_0", attraction_type="Museum")

    >>> # Usage Example:
    filter_attractions(cache_key="search_attractions_results_0", min_rating=4.5)

    >>> # Usage Example:
    filter_attractions(cache_key="search_attractions_results_0", state="NY", attraction_type="Park")

    Returns:
        SearchResultsOutputModel: Output containing the filtered results and query summary.
    """
    try:
        request = FilterAttractionsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"Input validation error: {str(e)}",
        )

    # Retrieve prior results from cache
    print(
        f"[filter_attractions] Calling get_results_from_cache with key='{request.cache_key}'"
    )
    prior_results = get_results_from_cache(key=request.cache_key)
    if prior_results is not None:
        _count = (
            len(prior_results.search_results)
            if hasattr(prior_results, "search_results")
            else len(prior_results.get("search_results", []))
        )
        print(f"[filter_attractions] ✅ [CACHE LOADED] Cache returned {_count} item(s)")
    if prior_results is None:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"Error: No cached results found for key '{request.cache_key}'.",
        )

    if hasattr(prior_results, "model_dump"):
        prior_results_dict = prior_results.model_dump()
    else:
        prior_results_dict = prior_results

    prior_attractions = prior_results_dict.get("search_results", [])
    if not prior_attractions:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary="Found 0 attraction(s) matching the filters.",
        )

    df = pd.DataFrame(prior_attractions)

    if df.empty:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary="Found 0 attraction(s) matching the filters.",
        )

    mask = pd.Series(True, index=df.index)

    if request.city is not None and "city" in df.columns:
        mask &= df["city"].astype(str).str.lower() == request.city.lower()

    if request.state is not None and "state" in df.columns:
        mask &= df["state"].astype(str).str.lower() == request.state.lower()

    if request.attraction_type is not None and "type" in df.columns:
        mask &= df["type"].astype(str).str.lower() == request.attraction_type.lower()

    if request.min_rating is not None and "rating" in df.columns:
        mask &= pd.to_numeric(df["rating"], errors="coerce") >= request.min_rating

    if request.max_rating is not None and "rating" in df.columns:
        mask &= pd.to_numeric(df["rating"], errors="coerce") <= request.max_rating

    filtered_df = df[mask].sort_values(
        by=["rating", "city", "name"],
        ascending=[False, True, True],
    )

    allowed_fields = set(Attraction.model_fields.keys())
    attractions = [
        Attraction.model_validate(
            {key: value for key, value in record.items() if key in allowed_fields}
        ).model_dump()
        for record in filtered_df.to_dict(orient="records")
    ]

    return SearchResultsOutputModel(
        search_results=attractions,
        query_summary=f"Found {len(attractions)} attraction(s) matching the filters.",
    )
