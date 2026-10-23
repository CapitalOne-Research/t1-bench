import re

import pandas as pd

from t1_plus_plus.schema.dessert.filter_bakeries import FilterBakeriesInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.tools.dessert.search_bakeries import summarize_query
from t1_plus_plus.tools.general.cache import get_results_from_cache


def filter_bakeries(**kwargs: FilterBakeriesInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to apply additional filters to an existing list of bakeries
        based on criteria such as neighborhood, budget, ratings, bread specialties,
        service options, and dietary options.

    Important:
        Before calling this tool, you MUST first call `get_results_from_cache` to retrieve the prior
        search results using the cache key from the previous search. Pass the cache key into the
        `cache_key` parameter of this tool.

    Examples:
    >>> # Usage Example:
    filter_bakeries(cache_key="search_bakeries_results_0", has_sourdough=True, has_wedding_cakes=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting filtered bakeries as well as the summary.
    """
    try:
        search_input = FilterBakeriesInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    # Retrieve prior results from cache
    print(f"[filter_bakeries] Calling get_results_from_cache with key='{search_input.cache_key}'")
    prior_results = get_results_from_cache(key=search_input.cache_key)
    if prior_results is not None:
        _count = len(prior_results.search_results) if hasattr(prior_results, "search_results") else len(prior_results.get("search_results", []))
        print(f"[filter_bakeries] Cache returned {_count} item(s)")
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

    all_bakeries_df = pd.DataFrame(prior_search_results)

    if len(all_bakeries_df) == 0:
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
            query_summary=f"{complete_query}\nThere are 0 bakery(s) that matched this query!",
        )

    mask = pd.Series(True, index=all_bakeries_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "neighborhood":
            mask &= all_bakeries_df["neighborhood"].isin(search_query_parameters)

        elif col == "bakery_name":
            if "name" in all_bakeries_df.columns:
                mask &= all_bakeries_df["name"].isin(search_query_parameters)

        elif col == "bakery_id":
            if "id" in all_bakeries_df.columns:
                mask &= all_bakeries_df["id"].isin(search_query_parameters)

        elif col == "rating":
            mask &= (all_bakeries_df["rating"] >= search_query_parameters[0]) & (
                all_bakeries_df["rating"] <= search_query_parameters[1]
            )

        elif col == "budget":
            mask &= all_bakeries_df["price_per_person"] <= search_query_parameters

        elif col == "price_level":
            if "price_level" in all_bakeries_df.columns:
                mask &= all_bakeries_df["price_level"].isin(search_query_parameters)

        elif col.startswith("has_"):
            if col in all_bakeries_df.columns:
                if all_bakeries_df[col].dtype == object:
                    mask &= all_bakeries_df[col].astype(str).str.lower() == str(
                        search_query_parameters
                    ).lower()
                else:
                    mask &= all_bakeries_df[col] == search_query_parameters

    resulting_bakeries = (all_bakeries_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)

    prior_summary = prior_results_dict.get("query_summary", "")
    prior_summary = re.sub(
        r"There are.*?that matched this query!\.?$", "", prior_summary.strip()
    )
    complete_query = f"{prior_summary}\nAdditionally filtering for {summarized_query}"

    if len(resulting_bakeries) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_bakeries,
            query_summary=f"{complete_query}\nThere are 0 bakery(s) that matched this query!",
        )
    final_results = resulting_bakeries[:10]
    return SearchResultsOutputModel(
        search_results=final_results,
        query_summary=f"{complete_query}\nThere are {len(final_results)} bakery(s) that matched this query!",
    )
