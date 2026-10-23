import pandas as pd
import re
from pathlib import Path

from t1_plus_plus.schema.cruise.filter_cruises import FilterCruisesInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.tools.cruise.search_cruises import summarize_cruise_query, all_cruises_df
from t1_plus_plus.tools.general.cache import get_results_from_cache

def filter_cruises(**kwargs: FilterCruisesInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Refine an existing cruise result set based on additional criteria.

    Important:
        Before calling this tool, you MUST first call `get_results_from_cache` to retrieve the cache key
        for the prior search results. Pass the cache key into the `cache_key` parameter of this tool.

    Examples:
    >>> # Usage Example:
    filter_cruises(cache_key="search_cruises_results_0", cabin_type="balcony", price_per_person_max=2000)

    >>> # Usage Example:
    filter_cruises(cache_key="search_cruises_results_0", has_wifi=True, beverages_included=True)

    >>> # Usage Example:
    filter_cruises(cache_key="filter_cruises_results_0", rating=[4.0, 5.0], is_adults_only=True)
    """

    # Gatekeeper for the "filters" hallucination
    if "filters" in kwargs and isinstance(kwargs["filters"], dict):
        for key, value in kwargs["filters"].items():
            kwargs[key] = value
        del kwargs["filters"]

    try:
        search_input = FilterCruisesInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    prior_results = get_results_from_cache(key=search_input.cache_key)
    if prior_results is None:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"Error: No cached results found for key '{search_input.cache_key}'.",
        )

    if hasattr(prior_results, "model_dump"):
        prior_results_dict = prior_results.model_dump()
    else:
        prior_results_dict = prior_results

    prior_cruises = prior_results_dict.get("search_results", [])

    search_input_filtered = {k: v for k, v in search_input.model_dump().items() if v is not None and k != "cache_key"}

    prior_summary = prior_results_dict.get("query_summary") or ""
    prior_summary = re.sub(r"There are.*?matched this query!\.?$", "", prior_summary.strip())

    if not prior_cruises:
        summarized_query = summarize_cruise_query({k: v for k, v in search_input_filtered.items()})
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{prior_summary}\nAdditionally filtering for {summarized_query}\nThere are 0 cruise(s) that matched this query!"
        )

    # Hydrate full records from the dataset using cruise_ids from prior results
    prior_ids = [item.get("cruise_id") for item in prior_cruises if item.get("cruise_id")]

    if all_cruises_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Error: Database is currently unavailable."
        )

    df = all_cruises_df[all_cruises_df["cruise_id"].isin(prior_ids)]
    mask = pd.Series(True, index=df.index)

    for col, val in search_input_filtered.items():
        if col == "destination":
            mask &= df["destination"].str.contains(val, case=False, na=False)
        elif col == "departure_port":
            mask &= df["departure_port"].str.lower() == val.lower()
        elif col == "cruise_line":
            mask &= df["cruise_line"].isin(val)
        elif col == "duration_nights":
            mask &= df["duration_nights"].isin(val)
        elif col == "tier":
            mask &= df["tier"] == val
        elif col == "rating":
            mask &= (df["rating"] >= val[0]) & (df["rating"] <= val[1])
        elif col == "price_per_person_max":
            cabin_raw = search_input_filtered.get("cabin_type", "interior")
            price_col = f"{cabin_raw}_price_per_person"
            if price_col in df.columns:
                mask &= df[price_col] <= val
        elif col == "cabin_type":
            avail_col = f"{val}_available"
            if avail_col in df.columns:
                mask &= df[avail_col] > 0
        elif col.startswith("has_") or col.startswith("is_") or col.endswith("_included"):
            if col in df.columns:
                mask &= df[col] == val

    resulting_cruises = df[mask].to_dict(orient="records")
    summarized_query = summarize_cruise_query({k: v for k, v in search_input_filtered.items()})

    complete_query = f"{prior_summary}\nAdditionally filtering for {summarized_query}"

    if len(resulting_cruises) == 0:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 cruise(s) that matched this query!"
        )

    top_10 = resulting_cruises[:10]

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
        query_summary=f"{complete_query}\nThere are {len(extracted_results)} cruise(s) that matched this query!"
    )
