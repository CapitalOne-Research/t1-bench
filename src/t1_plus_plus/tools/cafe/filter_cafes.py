import re

import pandas as pd

from t1_plus_plus.schema.cafe.filter_cafes import FilterCafesInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.tools.cafe.search_cafes import summarize_query
from t1_plus_plus.tools.general.cache import get_results_from_cache


def filter_cafes(**kwargs: FilterCafesInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to apply additional filters to an existing list of cafes based on
        criteria such as cafe type, neighborhood, budget, ratings, and various features
        (like milk alternatives, roast types, tea bases, toppings, etc.).

    Important:
        Before calling this tool, you MUST first call `get_results_from_cache` to retrieve the prior
        search results using the cache key from the previous search. Pass the cache key into the
        `cache_key` parameter of this tool.

    Examples:
    >>> # Usage Example:
    filter_cafes(cache_key="search_cafes_results_0", cafe_type="Coffee Shop", has_oat=True)

    >>> # Usage Example:
    filter_cafes(cache_key="search_cafes_results_0", rating=[4.0, 5.0], has_matcha=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting filtered cafes as well as the summary.
    """
    try:
        search_input = FilterCafesInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    # Retrieve prior results from cache
    print(f"[filter_cafes] Calling get_results_from_cache with key='{search_input.cache_key}'")
    prior_results = get_results_from_cache(key=search_input.cache_key)
    if prior_results is not None:
        _count = len(prior_results.search_results) if hasattr(prior_results, "search_results") else len(prior_results.get("search_results", []))
        print(f"[filter_cafes] Cache returned {_count} item(s)")
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

    all_cafes_df = pd.DataFrame(prior_search_results)

    if len(all_cafes_df) == 0:
        summarized_query = summarize_query(search_input_filtered)
        prior_summary = prior_results_dict.get("query_summary", "")
        prior_summary = re.sub(
            r"There are.*?that matched this query!\.?$", "", prior_summary.strip()
        )
        complete_query = (
            f"{prior_summary}\nAdditionally filtering for {summarized_query}"
        )
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 cafe(s) that matched this query!",
        )

    mask = pd.Series(True, index=all_cafes_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "cafe_type":
            if "cafe_type" in all_cafes_df.columns:
                mask &= all_cafes_df["cafe_type"] == search_query_parameters

        elif col == "neighborhood":
            mask &= all_cafes_df["neighborhood"].isin(search_query_parameters)

        elif col == "cafe_name":
            mask &= all_cafes_df["name"].isin(search_query_parameters)

        elif col == "cafe_id":
            mask &= all_cafes_df["id"].isin(search_query_parameters)

        elif col == "rating":
            mask &= (all_cafes_df["rating"] >= search_query_parameters[0]) & (
                all_cafes_df["rating"] <= search_query_parameters[1]
            )

        elif col == "budget":
            mask &= all_cafes_df["price_per_person"] <= search_query_parameters

        elif col == "price_level":
            if "price_level" in all_cafes_df.columns:
                mask &= all_cafes_df["price_level"].isin(search_query_parameters)

        elif col.startswith("has_"):
            if col in all_cafes_df.columns:
                if all_cafes_df[col].dtype == object:
                    mask &= all_cafes_df[col].astype(str).str.lower() == str(
                        search_query_parameters
                    ).lower()
                else:
                    mask &= all_cafes_df[col] == search_query_parameters

    resulting_cafes = (all_cafes_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)

    prior_summary = prior_results_dict.get("query_summary", "")
    prior_summary = re.sub(
        r"There are.*?that matched this query!\.?$", "", prior_summary.strip()
    )
    complete_query = f"{prior_summary}\nAdditionally filtering for {summarized_query}"

    if len(resulting_cafes) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_cafes,
            query_summary=f"{complete_query}\nThere are 0 cafe(s) that matched this query!",
        )
    final_results = resulting_cafes[:10]
    return SearchResultsOutputModel(
        search_results=final_results,
        query_summary=f"{complete_query}\nThere are {len(final_results)} cafe(s) that matched this query!",
    )
