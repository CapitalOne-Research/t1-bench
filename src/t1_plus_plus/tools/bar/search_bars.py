from datetime import datetime

import pandas as pd
from pathlib import Path
from t1_plus_plus.schema.bar.search_bars import SearchBarsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

# Load the CSV
data_dir = Path(__file__).resolve().parents[4] / "datasets"
CSV_PATH = str(data_dir / "data_bar_lounge.csv")
try:
    all_bars_df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    all_bars_df = pd.DataFrame()

# Convert opening and closing times to datetime.time for easier comparison
if not all_bars_df.empty:
    if "opening_time" in all_bars_df.columns:
        all_bars_df["opening_time"] = pd.to_datetime(
            all_bars_df["opening_time"], format="%H:%M", errors="coerce"
        ).dt.time
    if "closing_time" in all_bars_df.columns:
        all_bars_df["closing_time"] = pd.to_datetime(
            all_bars_df["closing_time"], format="%H:%M", errors="coerce"
        ).dt.time


def summarize_query(search_input_filtered):
    result = []

    # Core Location
    if "city" in search_input_filtered:
        result.append("Bar search results in {},".format(search_input_filtered["city"]))

    if "neighborhood" in search_input_filtered:
        neighborhoods = ", ".join(search_input_filtered["neighborhood"])
        result.append("in neighborhood(s) [{}],".format(neighborhoods))

    # Identifiers
    if "bar_name" in search_input_filtered:
        names = ", ".join(search_input_filtered["bar_name"])
        result.append("for bar(s) [{}],".format(names))

    if "bar_id" in search_input_filtered:
        ids = ", ".join(search_input_filtered["bar_id"])
        result.append("with ID(s) [{}],".format(ids))
    
    if "bar_type" in search_input_filtered:
        types = ", ".join(search_input_filtered["bar_type"])
        result.append("of type(s) [{}],".format(types))

    # Numeric Ranges & Constraints
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

    # Collect and format boolean features
    features = [
        k
        for k, v in search_input_filtered.items()
        if (k.startswith("has_") or k.startswith("is_")) and v is True
    ]
    if features:
        feature_names = ", ".join(
            [
                f.replace("has_", "").replace("is_", "").replace("_", " ")
                for f in features
            ]
        )
        result.append("with features: [{}],".format(feature_names))

    final_result = " ".join(result)
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."

    return final_result


def search_bars(**kwargs: SearchBarsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for bars or lounges based on several criteria such as city, neighborhood, budget, ratings, and various venue features (like happy hour, live music, vegan options, etc.). Note - 'city' MUST be provided.

    Examples:
    >>> # Usage Example:
    search_bars(city="New York", neighborhood=["Manhattan", "Brooklyn"], budget=50, has_live_music=True)

    >>> # Usage Example:
    search_bars(city="Los Angeles", rating=[4.0, 5.0], time_range=["22:00", "02:00"], has_vip_lounge=True)

    >>> # Usage Example:
    search_bars(city="Chicago", has_craft_beer=True, has_sports_games=True, minimum_age=21)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting bars as well as the summary.
    """
    try:
        search_input = SearchBarsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    search_input_filtered = {
        k: v for k, v in search_input.model_dump().items() if v is not None
    }

    if all_bars_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    mask = pd.Series(True, index=all_bars_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "city":
            mask &= all_bars_df["city"] == search_query_parameters

        elif col == "neighborhood":
            mask &= all_bars_df["neighborhood"].isin(search_query_parameters)

        elif col == "bar_name":
            # Map input 'bar_name' to the dataframe 'name' column
            mask &= all_bars_df["name"].isin(search_query_parameters)

        elif col == "bar_id":
            # Map input 'bar_id' to the dataframe 'id' column
            mask &= all_bars_df["id"].isin(search_query_parameters)
        
        elif col == "bar_type":
            if "bar_type" in all_bars_df.columns:
                mask &= all_bars_df["bar_type"].isin(search_query_parameters)

        elif col == "rating":
            mask &= (all_bars_df["rating"] >= search_query_parameters[0]) & (
                all_bars_df["rating"] <= search_query_parameters[1]
            )

        elif col == "budget":
            # Map input 'budget' to the dataframe 'price_per_person' column
            if "price_per_person" in all_bars_df.columns:
                mask &= all_bars_df["price_per_person"] <= search_query_parameters

        elif col == "cover_fee_max":
            if "cover_fee" in all_bars_df.columns:
                mask &= all_bars_df["cover_fee"] <= search_query_parameters

        elif col == "event_occupancy":
            if "event_occupancy" in all_bars_df.columns:
                mask &= all_bars_df["event_occupancy"] <= search_query_parameters

        elif col == "minimum_age":
            if "minimum_age" in all_bars_df.columns:
                mask &= all_bars_df["minimum_age"] <= search_query_parameters

        elif col == "time_range":
            # search_query_parameters is ["HH:MM", "HH:MM"] normalized by validator
            start_time_str = search_query_parameters[0]
            end_time_str = search_query_parameters[1]

            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            def is_open(row):
                op = row.get("opening_time")
                cl = row.get("closing_time")

                # Check for NaT/NaN
                if pd.isna(op) or pd.isna(cl):
                    return False

                # Normal operating hours (e.g., 08:00 to 22:00)
                if op <= cl:
                    return op <= start_time and cl >= end_time
                # Overnight operating hours (e.g., 20:00 to 02:00)
                else:
                    if start_time >= op or end_time <= cl:
                        return True
                    return False

            mask &= all_bars_df.apply(is_open, axis=1)

        # Dynamic Boolean Flags
        elif col.startswith("has_") or col.startswith("is_"):
            if col in all_bars_df.columns:
                mask &= all_bars_df[col] == search_query_parameters

    resulting_bars = (all_bars_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)

    if len(resulting_bars) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_bars,
            query_summary=f"{summarized_query}\nThere are 0 bar(s) that matched this query!",
        )

    top_10 = resulting_bars[:10]

    extracted_results = [
        {
            "bar_id": item.get("id"),  # Extracted from 'id' to 'bar_id'
            "name": item.get("name"),
            "city": item.get("city"),
            "state": item.get("state"),
            "neighborhood": item.get("neighborhood"),
            "bar_type": item.get("bar_type"),
            "rating": item.get("rating"),
            "budget": item.get("price_per_person"),
        }
        for item in top_10
    ]

    return SearchResultsOutputModel(
        search_results=extracted_results,
        query_summary=f"{summarized_query}\nThere are {len(extracted_results)} bar(s) that matched this query!",
    )