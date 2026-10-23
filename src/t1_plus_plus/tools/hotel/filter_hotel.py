import re

import pandas as pd

import t1_plus_plus.tools.hotel.search_hotel as sh
from t1_plus_plus.schema.hotel.filter_hotel import FilterHotelInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.tools.general.cache import get_results_from_cache


def summarize_query(search_input_filtered):
    result = []

    if "neighborhood" in search_input_filtered:
        neighborhoods = ", ".join(search_input_filtered["neighborhood"])
        result.append("in neighborhood(s) [{}],".format(neighborhoods))

    if "hotel_name" in search_input_filtered:
        names = ", ".join(search_input_filtered["hotel_name"])
        result.append("for hotel(s) [{}],".format(names))

    if "hotel_id" in search_input_filtered:
        ids = ", ".join(search_input_filtered["hotel_id"])
        result.append("with ID(s) [{}],".format(ids))

    if "brand" in search_input_filtered:
        brands = ", ".join(search_input_filtered["brand"])
        result.append("of brand(s) [{}],".format(brands))

    if "star_rating" in search_input_filtered:
        rating = search_input_filtered["star_rating"]
        result.append("star rating between {} and {},".format(rating[0], rating[1]))

    features = [
        k
        for k, v in search_input_filtered.items()
        if (k.startswith("has_") or k.startswith("is_")) and v is True
    ]
    if features:
        feature_names = ", ".join(
            [f.replace("has_", "").replace("is_", "").replace("_", " ") for f in features]
        )
        result.append("with features: [{}],".format(feature_names))

    final_result = " ".join(result)
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."
    return final_result


def filter_hotel(**kwargs) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to apply additional filters to an existing list of hotels based on criteria such as neighborhood, brand, star ratings, and various venue features (like pool, gym, pet friendly, etc.).

    Important:
        Before calling this tool, you MUST first call `get_results_from_cache` to retrieve the prior
        search results using the cache key from the previous search. Pass the cache key into the
        `cache_key` parameter of this tool.

    Examples:
    >>> # Usage Example:
    filter_hotel(cache_key="previous_hotels", neighborhood=["Manhattan", "Brooklyn"])

    >>> # Usage Example:
    filter_hotel(cache_key="previous_hotels", brand=["Aura", "Verve"], is_pet_friendly=True)

    >>> # Usage Example:
    filter_hotel(cache_key="previous_hotels", star_rating=[4.0, 5.0], has_pool=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting filtered hotels as well as the summary.
    """
    try:
        search_input = FilterHotelInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    # Retrieve prior results from cache
    print(f"[filter_hotel] Calling get_results_from_cache with key='{search_input.cache_key}'")
    prior_results = get_results_from_cache(key=search_input.cache_key)
    if prior_results is not None:
        _count = len(prior_results.search_results) if hasattr(prior_results, "search_results") else len(prior_results.get("search_results", []))
        print(f"[filter_hotel] Cache returned {_count} item(s)")
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

    summarized_query = summarize_query(search_input_filtered)
    complete_query = (
        f"{prior_summary}\nAdditionally filtering for {summarized_query}"
        if summarized_query
        else prior_summary
    )

    if not prior_search_results:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 hotel(s) that matched this query!",
        )

    # Hydrate: collect hotel_ids from prior results, fetch full rows from master CSV
    prior_ids = [
        item.get("hotel_id")
        for item in prior_search_results
        if isinstance(item, dict) and item.get("hotel_id")
    ]

    if sh.all_hotels_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    current_df = sh.all_hotels_df[sh.all_hotels_df["hotel_id"].isin(prior_ids)].copy()

    if current_df.empty:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 hotel(s) that matched this query!",
        )

    # Apply filters against the full master rows
    mask = pd.Series(True, index=current_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "neighborhood":
            mask &= current_df["neighborhood"].isin(search_query_parameters)

        elif col == "hotel_name":
            if "hotel_name" in current_df.columns:
                mask &= current_df["hotel_name"].isin(search_query_parameters)

        elif col == "hotel_id":
            if "hotel_id" in current_df.columns:
                mask &= current_df["hotel_id"].isin(search_query_parameters)

        elif col == "brand":
            if "brand" in current_df.columns:
                mask &= current_df["brand"].isin(search_query_parameters)

        elif col == "star_rating":
            mask &= (current_df["star_rating"] >= search_query_parameters[0]) & (
                current_df["star_rating"] <= search_query_parameters[1]
            )

        elif col.startswith("has_") or col.startswith("is_"):
            if col in current_df.columns:
                if current_df[col].dtype == object:
                    mask &= (
                        current_df[col].astype(str).str.lower()
                        == str(search_query_parameters).lower()
                    )
                else:
                    mask &= current_df[col] == search_query_parameters

    resulting_hotels = current_df[mask]

    if len(resulting_hotels) == 0:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 hotel(s) that matched this query!",
        )

    # Return slim summary fields (same shape as search_hotel output)
    extracted_results = [
        {
            "hotel_id": row.get("hotel_id"),
            "hotel_name": row.get("hotel_name"),
            "city": row.get("city"),
            "state": row.get("state"),
            "neighborhood": row.get("neighborhood"),
            "brand": row.get("brand"),
            "star_rating": row.get("star_rating"),
        }
        for row in resulting_hotels.head(10).to_dict(orient="records")
    ]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{complete_query}\nThere are {len(extracted_results)} hotel(s) that matched this query!",
    )
