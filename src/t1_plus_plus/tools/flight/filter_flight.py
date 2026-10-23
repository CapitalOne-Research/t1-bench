import re

import pandas as pd

from t1_plus_plus.schema.flight.filter_flights import FilterFlightsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
import t1_plus_plus.tools.flight.search_flight as sf
from t1_plus_plus.tools.general.cache import get_results_from_cache


def summarize_filter_query(search_input_filtered):
    result = []

    if "departure_city" in search_input_filtered:
        result.append(
            f"departing from city '{search_input_filtered['departure_city']}',"
        )
    if "arrival_city" in search_input_filtered:
        result.append(f"arriving at city '{search_input_filtered['arrival_city']}',")
    if "departure_airport" in search_input_filtered:
        result.append(f"departing from '{search_input_filtered['departure_airport']}',")
    if "arrival_airport" in search_input_filtered:
        result.append(f"arriving at '{search_input_filtered['arrival_airport']}',")
    if "departure_date" in search_input_filtered:
        result.append(f"on date {search_input_filtered['departure_date']},")
    if "arrival_date" in search_input_filtered:
        result.append(f"arriving on {search_input_filtered['arrival_date']},")
    if "airline" in search_input_filtered:
        airlines = ", ".join(search_input_filtered["airline"])
        result.append(f"with airlines [{airlines}],")
    if "price_max" in search_input_filtered:
        result.append(f"max price ${search_input_filtered['price_max']},")
    if "departure_time_after" in search_input_filtered:
        result.append(
            f"departing after {search_input_filtered['departure_time_after']},"
        )
    if "departure_time_before" in search_input_filtered:
        result.append(
            f"departing before {search_input_filtered['departure_time_before']},"
        )
    if "ticket_class" in search_input_filtered:
        result.append(f"ticket class '{search_input_filtered['ticket_class']}',")

    final_result = " ".join(result)
    return final_result.rstrip(",") + "." if final_result else ""


def filter_flight(**kwargs: FilterFlightsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to apply filters to an existing list of flights based on criteria
        such as airline, price, departure time, ticket class, and dates.

    Examples:
    >>> # Usage Example:
    filter_flight(cache_key="previous_flights", airline=["AeroOne", "SkyReach Airways"])

    >>> # Usage Example:
    filter_flight(cache_key="previous_flights", price_max=300.0, ticket_class="Economy")

    >>> # Usage Example:
    filter_flight(cache_key="previous_flights", departure_time_after="08:00", departure_time_before="14:00")

    Returns:
        SearchResultsOutputModel: Output object containing the resulting filtered flights and a query summary.
    """
    try:
        search_input = FilterFlightsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    # Retrieve prior results from cache
    print(
        f"[filter_flight] Calling get_results_from_cache with key='{search_input.cache_key}'"
    )
    prior_results = get_results_from_cache(key=search_input.cache_key)
    if prior_results is not None:
        _count = (
            len(prior_results.search_results)
            if hasattr(prior_results, "search_results")
            else len(prior_results.get("search_results", []))
        )
        print(f"[filter_flight] ✅ [CACHE LOADED] Cache returned {_count} item(s)")
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

    summarized_query = summarize_filter_query(search_input_filtered)
    complete_query = (
        f"{prior_summary}\nAdditionally filtering for {summarized_query}"
        if summarized_query
        else prior_summary
    )

    if not prior_search_results:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 flight(s) that matched this query!",
        )

    # Hydrate from the global DataFrame using IDs from prior results
    prior_ids = [
        item.get("flight_id") for item in prior_search_results if item.get("flight_id")
    ]
    current_df = sf.all_flights_df[sf.all_flights_df["flight_id"].isin(prior_ids)]

    if current_df.empty:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 flight(s) that matched this query!",
        )

    mask = pd.Series(True, index=current_df.index)

    for col, val in search_input_filtered.items():
        if col == "airline":
            mask &= current_df["airline"].isin(val)
        elif col == "price_max":
            mask &= current_df["price"] <= val
        elif col == "departure_time_after":
            mask &= current_df["departure_time"] >= val
        elif col == "departure_time_before":
            mask &= current_df["departure_time"] <= val
        elif col == "ticket_class":
            mask &= current_df["ticket_class"].str.lower() == val.lower()
        elif col == "departure_date":
            mask &= current_df["departure_date"] == val
        elif col == "arrival_date":
            mask &= current_df["arrival_date"] == val
        elif col == "departure_airport":
            mask &= current_df["departure_airport"].str.upper() == val.upper()
        elif col == "arrival_airport":
            mask &= current_df["arrival_airport"].str.upper() == val.upper()
        elif col == "departure_city":
            mask &= current_df["departure_city"].str.lower() == val.lower()
        elif col == "arrival_city":
            mask &= current_df["arrival_city"].str.lower() == val.lower()

    resulting_flights = current_df[mask].to_dict(orient="records")

    if len(resulting_flights) == 0:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nThere are 0 flight(s) that matched this query!",
        )

    final_results = resulting_flights[:10]
    return SearchResultsOutputModel(
        search_results=final_results,
        query_summary=f"{complete_query}\nThere are {len(final_results)} flight(s) that matched this query!",
    )
