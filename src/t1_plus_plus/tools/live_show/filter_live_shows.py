import re
from datetime import datetime

import pandas as pd

# IMPORTANT: Import the entire module, not the specific variable!
import t1_plus_plus.tools.live_show.search_live_shows as sls
from t1_plus_plus.schema.live_show.filter_live_shows import FilterLiveShowsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel
from t1_plus_plus.tools.general.cache import get_results_from_cache


def summarize_query(search_input_filtered: dict) -> str:
    """Helper to summarize the additional filters applied."""
    result = []

    if "live_event_id" in search_input_filtered:
        ids = ", ".join(search_input_filtered["live_event_id"])
        result.append(f"with ID(s) [{ids}]")

    if "neighborhood" in search_input_filtered:
        neighborhoods = ", ".join(search_input_filtered["neighborhood"])
        result.append(f"in neighborhood(s) [{neighborhoods}]")

    if "venue_type" in search_input_filtered:
        v_types = ", ".join(search_input_filtered["venue_type"])
        result.append(f"for venue type(s) [{v_types}]")

    if "event_category" in search_input_filtered:
        cats = ", ".join(search_input_filtered["event_category"])
        result.append(f"categorized as [{cats}]")

    if "show_name" in search_input_filtered:
        result.append(f"named '{search_input_filtered['show_name']}'")

    if "performer" in search_input_filtered:
        result.append(f"performed by {search_input_filtered['performer']}")

    if "seat_location" in search_input_filtered:
        locs = ", ".join(search_input_filtered["seat_location"])
        result.append(f"with availability in [{locs}] sections")

    if "price_range" in search_input_filtered:
        prices = search_input_filtered["price_range"]
        result.append(f"with tickets between ${prices[0]} and ${prices[1]}")

    if "event_date_range" in search_input_filtered:
        dates = " to ".join(search_input_filtered["event_date_range"])
        result.append(f"occurring between {dates}")

    if "time_range" in search_input_filtered:
        times = " to ".join(search_input_filtered["time_range"])
        result.append(f"starting between {times}")

    # Boolean Features
    features = []
    boolean_lookups = {
        "is_outdoors": "outdoors",
        "parking_available": "parking",
        "serves_food": "food service",
        "serves_alcohol": "alcohol service",
        "family_friendly": "family friendly"
    }
    for key, label in boolean_lookups.items():
        if search_input_filtered.get(key) is True:
            features.append(label)
    
    if features:
        result.append(f"with features: [{', '.join(features)}]")

    if not result:
        return ""

    final_result = ", ".join(result)
    return final_result


def filter_live_shows(**kwargs: FilterLiveShowsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to apply additional filters to an existing list of live shows based on criteria such as seat location, price range, venue amenities, event category, and show details.

    Examples:
    >>> # Usage Example:
    filter_live_shows(cache_key="cache_key_name_1", seat_location=["front"], price_range=[0, 150])

    >>> # Usage Example:
    filter_live_shows(cache_key="cache_key_name_0", family_friendly=True, serves_food=True, parking_available=True)

    >>> # Usage Example:
    filter_live_shows(cache_key="cache_key_name_1", event_category=["Jazz"], time_range=["18:00", "22:00"])

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting filtered live shows as well as the summary.
    """
    try:
        search_input = FilterLiveShowsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    # Retrieve prior results from cache
    print(f"[filter_live_shows] Calling get_results_from_cache with key='{search_input.cache_key}'")
    prior_results = get_results_from_cache(key=search_input.cache_key)
    if prior_results is not None:
        _count = len(prior_results.search_results) if hasattr(prior_results, "search_results") else len(prior_results.get("search_results", []))
        print(f"[filter_live_shows] Cache returned {_count} item(s)")
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

    if not prior_search_results:
        summarized_query = summarize_query(search_input_filtered)
        prior_summary = prior_results_dict.get("query_summary", "")
        if prior_summary:
            prior_summary = re.sub(
                r"Found \d+ show\(s\) matching your criteria\.?$", "", prior_summary.strip()
            )
        complete_query = f"{prior_summary}\nAdditionally filtering for {summarized_query}"
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nFound 0 show(s) matching your criteria.",
        )

    # 3. Hydrate IDs using live_event_id
    prior_ids = [
        item.get("live_event_id") or item.get("live_event_id")
        for item in prior_search_results
        if isinstance(item, dict) and (item.get("live_event_id"))
    ]

    # READ FROM THE MODULE DYNAMICALLY to get the mocked data
    if sls.all_shows_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    # 4. Filter the original DataFrame using live_event_id
    current_df = sls.all_shows_df[sls.all_shows_df["live_event_id"].isin(prior_ids)].copy()

    mask = pd.Series(True, index=current_df.index)
    requested_locs = search_input_filtered.get("seat_location")

    for col, val in search_input_filtered.items():
        if col in ("prior_results", "prior_search_query", "cache_key"):
            continue

        if col == "live_event_id":
            mask &= current_df["live_event_id"].isin(val)
        elif col == "neighborhood":
            mask &= current_df["Neighborhood"].isin(val)
        elif col == "venue_type":
            mask &= current_df["Venue_Type"].isin(val)
        elif col == "is_outdoors":
            mask &= current_df["Is_Outdoors"] == val
        elif col == "parking_available":
            mask &= current_df["Parking_Available"] == val
        elif col == "serves_food":
            mask &= current_df["Serves_Food"] == val
        elif col == "serves_alcohol":
            mask &= current_df["Serves_Alcohol"] == val
        elif col == "family_friendly":
            mask &= current_df["Family_Friendly"] == val
        elif col == "event_category":
            mask &= (current_df["Event_Category"].isin(val)) | (current_df["Primary_Event_Category"].isin(val))
        elif col == "show_name":
            mask &= current_df["Show_Name"].str.contains(val, case=False, na=False)
        elif col == "performer":
            mask &= current_df["Performer"].str.contains(val, case=False, na=False)

        # Seat Location Filter
        elif col == "seat_location":
            seat_mask = pd.Series(False, index=current_df.index)
            if "front" in val:
                seat_mask |= current_df["Front_Seats_Avail"] > 0
            if "middle" in val:
                seat_mask |= current_df["Middle_Seats_Avail"] > 0
            if "back" in val:
                seat_mask |= current_df["Back_Seats_Avail"] > 0
            mask &= seat_mask

        # Price Filtering
        elif col == "price_range":
            min_p, max_p = val[0], val[1]
            if requested_locs:
                price_mask = pd.Series(False, index=current_df.index)
                if "front" in requested_locs:
                    price_mask |= (current_df["Front_Price_USD"] >= min_p) & (current_df["Front_Price_USD"] <= max_p)
                if "middle" in requested_locs:
                    price_mask |= (current_df["Middle_Price_USD"] >= min_p) & (current_df["Middle_Price_USD"] <= max_p)
                if "back" in requested_locs:
                    price_mask |= (current_df["Back_Price_USD"] >= min_p) & (current_df["Back_Price_USD"] <= max_p)
                mask &= price_mask
            else:
                mask &= (
                    ((current_df["Front_Price_USD"] >= min_p) & (current_df["Front_Price_USD"] <= max_p)) |
                    ((current_df["Middle_Price_USD"] >= min_p) & (current_df["Middle_Price_USD"] <= max_p)) |
                    ((current_df["Back_Price_USD"] >= min_p) & (current_df["Back_Price_USD"] <= max_p))
                )

        # Date Filtering
        elif col == "event_date_range":
            start_d = datetime.strptime(val[0], "%Y-%m-%d").date()
            end_d = datetime.strptime(val[1], "%Y-%m-%d").date()
            mask &= (current_df["Event_Date"] >= start_d) & (current_df["Event_Date"] <= end_d)

        # Time Filtering
        elif col == "time_range":
            start_t = datetime.strptime(val[0], "%H:%M").time()
            end_t = datetime.strptime(val[1], "%H:%M").time()
            mask &= current_df["Start_Time"].apply(lambda t: pd.notna(t) and start_t <= t <= end_t)

    resulting_shows = current_df[mask].to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)

    # 5. Format the final output summary
    prior_summary = prior_results_dict.get("query_summary", "")
    if prior_summary:
        prior_summary = re.sub(
            r"Found \d+ show\(s\) matching your criteria\.?$", "", prior_summary.strip()
        )

    if summarized_query:
        complete_query = f"{prior_summary}\nAdditionally filtering for {summarized_query}"
    else:
        complete_query = prior_summary

    if not resulting_shows:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\nFound 0 show(s) matching your criteria.",
        )

    # 6. Map DataFrame columns back to API field names and return select fields
    extracted_results = [
        {
            "live_event_id": item.get("live_event_id"),
            "venue_id": item.get("Venue_ID"),  # Map Venue_ID -> venue_id
            "show_name": item.get("Show_Name"),
            "performer": item.get("Performer"),
            "venue_name": item.get("Venue_Name"),
            "city": item.get("City"),
            "neighborhood": item.get("Neighborhood"),
            "event_date": str(item.get("Event_Date")),
            "start_time": str(item.get("Start_Time")),
            "event_category": item.get("Event_Category"),
        }
        for item in resulting_shows[:10]
    ]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{complete_query}\nFound {len(extracted_results)} show(s) matching your criteria.",
    )