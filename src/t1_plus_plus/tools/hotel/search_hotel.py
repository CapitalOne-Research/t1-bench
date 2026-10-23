import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.hotel.search_hotel import SearchHotelInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
CSV_PATH = str(_data_dir / "data_hotel.csv")
try:
    all_hotels_df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    all_hotels_df = pd.DataFrame()


def summarize_query(search_input_filtered):
    result = []

    if "city" in search_input_filtered:
        result.append("Hotel search results in {},".format(search_input_filtered["city"]))

    if "state" in search_input_filtered:
        result.append("state {},".format(search_input_filtered["state"]))

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


def search_hotel(**kwargs: SearchHotelInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for hotels based on several criteria such as city, neighborhood, brand, star ratings, and various venue features (like pool, gym, pet friendly, etc.). Note - 'city' MUST be provided.

    Examples:
    >>> # Usage Example:
    search_hotel(city="New York", neighborhood=["Manhattan", "Brooklyn"], star_rating=[4.0, 5.0], has_pool=True)

    >>> # Usage Example:
    search_hotel(city="Los Angeles", brand=["Aura", "Verve"], is_pet_friendly=True)

    >>> # Usage Example:
    search_hotel(city="Chicago", has_gym=True, has_digital_key=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting hotels as well as the summary.
    """
    try:
        search_input = SearchHotelInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    search_input_filtered = {
        k: v for k, v in search_input.model_dump().items() if v is not None
    }

    if all_hotels_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    mask = pd.Series(True, index=all_hotels_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "city":
            mask &= all_hotels_df["city"] == search_query_parameters

        elif col == "state":
            mask &= all_hotels_df["state"] == search_query_parameters

        elif col == "neighborhood":
            mask &= all_hotels_df["neighborhood"].isin(search_query_parameters)

        elif col == "hotel_name":
            mask &= all_hotels_df["hotel_name"].isin(search_query_parameters)

        elif col == "hotel_id":
            mask &= all_hotels_df["hotel_id"].isin(search_query_parameters)

        elif col == "brand":
            if "brand" in all_hotels_df.columns:
                mask &= all_hotels_df["brand"].isin(search_query_parameters)

        elif col == "star_rating":
            mask &= (all_hotels_df["star_rating"] >= search_query_parameters[0]) & (
                all_hotels_df["star_rating"] <= search_query_parameters[1]
            )

        elif col.startswith("has_") or col.startswith("is_"):
            if col in all_hotels_df.columns:
                mask &= all_hotels_df[col] == search_query_parameters

    resulting_hotels = all_hotels_df[mask]
    summarized_query = summarize_query(search_input_filtered)

    if len(resulting_hotels) == 0:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{summarized_query}\nThere are 0 hotel(s) that matched this query!",
        )

    # Return only summary fields; filter_hotel re-hydrates from master CSV by hotel_id
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
        query_summary=f"{summarized_query}\nThere are {len(extracted_results)} hotel(s) that matched this query!",
    )
