from datetime import datetime
import pandas as pd
from pathlib import Path
from typing import Any

from t1_plus_plus.schema.live_show.search_live_shows import SearchLiveShowsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

SHOWS_CSV = Path(__file__).resolve().parents[4] / "datasets" / "data_live_events.csv"

all_shows_df = pd.read_csv(SHOWS_CSV)

# Data Pre-processing
all_shows_df["Event_Date"] = pd.to_datetime(all_shows_df["Event_Date"]).dt.date
all_shows_df["Start_Time"] = pd.to_datetime(all_shows_df["Start_Time"], format="%I:%M %p", errors="coerce").dt.time

def summarize_query(search_input_filtered):
    result = []

    # Core Location
    if "city" in search_input_filtered:
        result.append(f"Show results in {search_input_filtered['city']}")

    if "live_event_id" in search_input_filtered:
        ids = ", ".join(search_input_filtered["live_event_id"])
        result.append(f"with ID(s) [{ids}]")

    if "neighborhood" in search_input_filtered:
        neighborhoods = ", ".join(search_input_filtered["neighborhood"])
        result.append(f"in neighborhood(s) [{neighborhoods}]")

    # Show Specifics
    if "show_name" in search_input_filtered:
        result.append(f"named '{search_input_filtered['show_name']}'")

    if "performer" in search_input_filtered:
        result.append(f"performed by {search_input_filtered['performer']}")

    if "event_category" in search_input_filtered:
        cats = ", ".join(search_input_filtered["event_category"])
        result.append(f"categorized as [{cats}]")

    # Seat Location
    if "seat_location" in search_input_filtered:
        locs = ", ".join(search_input_filtered["seat_location"])
        result.append(f"with availability in the [{locs}] section(s)")

    # Numeric Ranges
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

    final_result = ", ".join(result) + "."
    return final_result

def search_live_shows(**kwargs: SearchLiveShowsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for live shows and events based on several criteria such as city, neighborhood, venue type, event category, pricing, seat location, and various venue amenities (like parking, food service, outdoor seating, etc.). Note - 'city' MUST be provided.

    Examples:
    >>> # Usage Example:
    search_live_shows(city="Corona", event_category=["Jazz"], seat_location=["front", "middle"])

    >>> # Usage Example:
    search_live_shows(city="Broken Arrow", price_range=[0, 200], seat_location=["back"], parking_available=True)

    >>> # Usage Example:
    search_live_shows(city="New York", event_date_range=["2026-06-01", "2026-12-31"], serves_food=True, family_friendly=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting live shows as well as the summary.
    """
    # Validate input
    try:
        search_input = SearchLiveShowsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    search_input_filtered = {
        k: v for k, v in search_input.model_dump().items() if v is not None
    }

    if all_shows_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    mask = pd.Series(True, index=all_shows_df.index)
    requested_locs = search_input_filtered.get("seat_location")

    for col, val in search_input_filtered.items():
        # ID Lookup
        if col == "live_event_id":
            mask &= all_shows_df["live_event_id"].isin(val)
        # Location Mapping
        elif col == "city":
            mask &= all_shows_df["City"] == val
        elif col == "neighborhood":
            mask &= all_shows_df["Neighborhood"].isin(val)
        
        # Venue Attributes
        elif col == "venue_type":
            mask &= all_shows_df["Venue_Type"].isin(val)
        elif col == "is_outdoors":
            mask &= all_shows_df["Is_Outdoors"] == val
        elif col == "parking_available":
            mask &= all_shows_df["Parking_Available"] == val
        elif col == "serves_food":
            mask &= all_shows_df["Serves_Food"] == val
        elif col == "serves_alcohol":
            mask &= all_shows_df["Serves_Alcohol"] == val

        # Show Attributes
        elif col == "event_category":
            mask &= (all_shows_df["Event_Category"].isin(val)) | (all_shows_df["Primary_Event_Category"].isin(val))
        elif col == "show_name":
            mask &= all_shows_df["Show_Name"].str.contains(val, case=False, na=False)
        elif col == "performer":
            mask &= all_shows_df["Performer"].str.contains(val, case=False, na=False)
        elif col == "family_friendly":
            mask &= all_shows_df["Family_Friendly"] == val

        # Seat Location Filter (checks if ANY requested section has availability)
        elif col == "seat_location":
            seat_mask = pd.Series(False, index=all_shows_df.index)
            if "front" in val:
                seat_mask |= all_shows_df["Front_Seats_Avail"] > 0
            if "middle" in val:
                seat_mask |= all_shows_df["Middle_Seats_Avail"] > 0
            if "back" in val:
                seat_mask |= all_shows_df["Back_Seats_Avail"] > 0
            mask &= seat_mask

        # Price Filtering
        elif col == "price_range":
            min_p, max_p = val[0], val[1]
            if requested_locs:
                # Only check prices for the requested seat locations
                price_mask = pd.Series(False, index=all_shows_df.index)
                if "front" in requested_locs:
                    price_mask |= (all_shows_df["Front_Price_USD"] >= min_p) & (all_shows_df["Front_Price_USD"] <= max_p)
                if "middle" in requested_locs:
                    price_mask |= (all_shows_df["Middle_Price_USD"] >= min_p) & (all_shows_df["Middle_Price_USD"] <= max_p)
                if "back" in requested_locs:
                    price_mask |= (all_shows_df["Back_Price_USD"] >= min_p) & (all_shows_df["Back_Price_USD"] <= max_p)
                mask &= price_mask
            else:
                # Default: check if ANY section fits
                mask &= (
                    ((all_shows_df["Front_Price_USD"] >= min_p) & (all_shows_df["Front_Price_USD"] <= max_p)) |
                    ((all_shows_df["Middle_Price_USD"] >= min_p) & (all_shows_df["Middle_Price_USD"] <= max_p)) |
                    ((all_shows_df["Back_Price_USD"] >= min_p) & (all_shows_df["Back_Price_USD"] <= max_p))
                )

        # Date Filtering
        elif col == "event_date_range":
            start_d = datetime.strptime(val[0], "%Y-%m-%d").date()
            end_d = datetime.strptime(val[1], "%Y-%m-%d").date()
            mask &= (all_shows_df["Event_Date"] >= start_d) & (all_shows_df["Event_Date"] <= end_d)

        # Time Filtering
        elif col == "time_range":
            start_t = datetime.strptime(val[0], "%H:%M").time()
            end_t = datetime.strptime(val[1], "%H:%M").time()
            mask &= all_shows_df["Start_Time"].apply(lambda t: pd.notna(t) and start_t <= t <= end_t)

    resulting_shows = all_shows_df[mask].to_dict(orient="records")
    summary = summarize_query(search_input_filtered)

    if not resulting_shows:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{summary}\nFound 0 show(s) matching your criteria.",
        )

    top_10 = resulting_shows[:10]

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
        for item in top_10
    ]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{summary}\nFound {len(extracted_results)} show(s) matching your criteria.",
    )