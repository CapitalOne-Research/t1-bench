import re

import pandas as pd
from datetime import datetime

import t1_plus_plus.tools.bar.search_bars as sb
from t1_plus_plus.schema.bar.filter_bars import FilterBarsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.tools.general.cache import get_results_from_cache


def summarize_query(search_input_filtered):
    result = []

    if "neighborhood" in search_input_filtered:
        neighborhoods = ", ".join(search_input_filtered["neighborhood"])
        result.append("in neighborhood(s) [{}],".format(neighborhoods))

    if "bar_name" in search_input_filtered:
        names = ", ".join(search_input_filtered["bar_name"])
        result.append("for bar(s) [{}],".format(names))

    if "bar_id" in search_input_filtered:
        ids = ", ".join(search_input_filtered["bar_id"])
        result.append("with ID(s) [{}],".format(ids))

    if "bar_type" in search_input_filtered:
        types = ", ".join(search_input_filtered["bar_type"])
        result.append("of type(s) [{}],".format(types))

    if "rating" in search_input_filtered:
        rating = search_input_filtered["rating"]
        result.append("rating between {} and {},".format(rating[0], rating[1]))

    if "budget" in search_input_filtered:
        result.append(
            "budget per person up to ${},".format(search_input_filtered["budget"])
        )

    if "cover_fee_max" in search_input_filtered:
        result.append(
            "maximum cover fee ${},".format(search_input_filtered["cover_fee_max"])
        )

    if "event_occupancy" in search_input_filtered:
        result.append(
            "max event occupancy {},".format(search_input_filtered["event_occupancy"])
        )

    if "minimum_age" in search_input_filtered:
        result.append(
            "minimum age requirement up to {},".format(
                search_input_filtered["minimum_age"]
            )
        )

    if "time_range" in search_input_filtered:
        times = " to ".join(search_input_filtered["time_range"])
        result.append("open between [{}],".format(times))

    # Collect and format boolean features (e.g., has_live_music, has_craft_beer)
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


def filter_bars(**kwargs: FilterBarsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to apply additional filters to an existing list of bars based on criteria such as neighborhood, budget, ratings, and various venue features (like happy hour, live music, vegan options, etc.).

    Important:
        Before calling this tool, you MUST first call `search_bars` so results are stored in the cache.
        Pass the cache key (e.g., 'previous_bars') into the `cache_key` parameter of this tool.

    Examples:
    >>> # Usage Example:
    filter_bars(cache_key="previous_bars", neighborhood=["Manhattan", "Brooklyn"])

    >>> # Usage Example:
    filter_bars(cache_key="previous_bars", budget=50, has_live_music=True, has_craft_beer=True)

    >>> # Usage Example:
    filter_bars(cache_key="previous_bars", rating=[4.0, 5.0], time_range=["22:00", "02:00"], has_vip_lounge=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting filtered bars as well as the summary.
    """
    try:
        search_input = FilterBarsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    # Retrieve prior results from cache
    print(
        f"[filter_bars] Calling get_results_from_cache with key='{search_input.cache_key}'"
    )
    prior_results = get_results_from_cache(key=search_input.cache_key)
    if prior_results is not None:
        _count = (
            len(prior_results.search_results)
            if hasattr(prior_results, "search_results")
            else len(prior_results.get("search_results", []))
        )
        print(f"[filter_bars] ✅ [CACHE LOADED] Cache returned {_count} item(s)")
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
            query_summary=f"{complete_query}\nThere are 0 bar(s) that matched this query!",
        )

    # Hydrate IDs from cache results against the master DataFrame
    prior_ids = [
        item.get("bar_id") for item in prior_search_results if item.get("bar_id")
    ]

    if sb.all_bars_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    current_df = sb.all_bars_df[sb.all_bars_df["id"].isin(prior_ids)]
    mask = pd.Series(True, index=current_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "neighborhood":
            mask &= current_df["neighborhood"].isin(search_query_parameters)

        elif col == "bar_name":
            if "name" in current_df.columns:
                mask &= current_df["name"].isin(search_query_parameters)

        elif col == "bar_id":
            if "id" in current_df.columns:
                mask &= current_df["id"].isin(search_query_parameters)

        elif col == "bar_type":
            if "bar_type" in current_df.columns:
                mask &= current_df["bar_type"].isin(search_query_parameters)

        elif col == "rating":
            mask &= (current_df["rating"] >= search_query_parameters[0]) & (
                current_df["rating"] <= search_query_parameters[1]
            )

        elif col == "budget":
            if "price_per_person" in current_df.columns:
                mask &= current_df["price_per_person"] <= search_query_parameters

        elif col == "cover_fee_max":
            if "cover_fee" in current_df.columns:
                mask &= current_df["cover_fee"] <= search_query_parameters

        elif col == "event_occupancy":
            if "event_occupancy" in current_df.columns:
                mask &= current_df["event_occupancy"] <= search_query_parameters

        elif col == "minimum_age":
            if "minimum_age" in current_df.columns:
                mask &= current_df["minimum_age"] <= search_query_parameters

        elif col == "time_range":
            start_time_str = search_query_parameters[0]
            end_time_str = search_query_parameters[1]

            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            def is_open(row):
                op = row.get("opening_time")
                cl = row.get("closing_time")

                if pd.isna(op) or pd.isna(cl):
                    return False

                if op <= cl:
                    return op <= start_time and cl >= end_time
                else:
                    if start_time >= op or end_time <= cl:
                        return True
                    return False

            mask &= current_df.apply(is_open, axis=1)

        elif col.startswith("has_") or col.startswith("is_"):
            if col in current_df.columns:
                if current_df[col].dtype == object:
                    mask &= (
                        current_df[col].astype(str).str.lower()
                        == str(search_query_parameters).lower()
                    )
                else:
                    mask &= current_df[col] == search_query_parameters

    resulting_bars = (current_df[mask]).to_dict(orient="records")

    if len(resulting_bars) == 0:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 bar(s) that matched this query!",
        )

    extracted_results = [
        {
            "bar_id": item.get("id"),
            "name": item.get("name"),
            "city": item.get("city"),
            "state": item.get("state"),
            "neighborhood": item.get("neighborhood"),
            "bar_type": item.get("bar_type"),
            "rating": item.get("rating"),
            "budget": item.get("price_per_person"),
        }
        for item in resulting_bars[:10]
    ]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{complete_query}\nThere are {len(extracted_results)} bar(s) that matched this query!",
    )
