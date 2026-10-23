import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.dessert.search_dessert_shops import SearchDessertShopsInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

data_dir = Path(__file__).resolve().parents[4] / "datasets"

CSV_PATH = str(data_dir / "data_dessert_shop.csv")
try:
    all_dessert_shops_df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    all_dessert_shops_df = pd.DataFrame()


def summarize_query(search_input_filtered):
    result = []

    if "city" in search_input_filtered:
        result.append("Dessert shop search results in {},".format(search_input_filtered["city"]))

    if "neighborhood" in search_input_filtered:
        neighborhoods = ", ".join(search_input_filtered["neighborhood"])
        result.append("in neighborhood(s) [{}],".format(neighborhoods))

    if "shop_name" in search_input_filtered:
        names = ", ".join(search_input_filtered["shop_name"])
        result.append("for shop(s) [{}],".format(names))

    if "shop_id" in search_input_filtered:
        ids = ", ".join(search_input_filtered["shop_id"])
        result.append("with ID(s) [{}],".format(ids))

    if "rating" in search_input_filtered:
        rating = search_input_filtered["rating"]
        result.append("rating between {} and {},".format(rating[0], rating[1]))

    if "budget" in search_input_filtered:
        result.append(
            "budget per person up to ${},".format(search_input_filtered["budget"])
        )

    if "price_level" in search_input_filtered:
        levels = ", ".join(search_input_filtered["price_level"])
        result.append("price level(s) [{}],".format(levels))

    features = [
        k
        for k, v in search_input_filtered.items()
        if (k.startswith("has_") or k.startswith("is_")) and v is True
    ]
    if features:
        feature_names = ", ".join(
            [f.replace("has_has_", "").replace("has_is_", "").replace("has_", "").replace("_", " ") for f in features]
        )
        result.append("with features: [{}],".format(feature_names))

    final_result = " ".join(result)
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."

    return final_result


def search_dessert_shops(**kwargs: SearchDessertShopsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for dessert shops based on criteria such as city,
        neighborhood, rating, price level, and various dessert categories, toppings,
        temperature profiles, dietary options, and features.
        Note - 'city' MUST be provided.

    Examples:
    >>> # Usage Example:
    search_dessert_shops(city="New York", has_ice_cream=True, has_is_vegan_friendly=True)

    >>> # Usage Example:
    search_dessert_shops(city="New York", rating=[4.0, 5.0], has_custom_cake_ordering=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting dessert shops as well as the summary.
    """
    try:
        search_input = SearchDessertShopsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    search_input_filtered = {
        k: v for k, v in search_input.model_dump().items() if v is not None
    }

    if all_dessert_shops_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    mask = pd.Series(True, index=all_dessert_shops_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "city":
            mask &= all_dessert_shops_df["city"] == search_query_parameters

        elif col == "neighborhood":
            mask &= all_dessert_shops_df["neighborhood"].isin(search_query_parameters)

        elif col == "shop_name":
            mask &= all_dessert_shops_df["name"].isin(search_query_parameters)

        elif col == "shop_id":
            mask &= all_dessert_shops_df["id"].isin(search_query_parameters)

        elif col == "rating":
            mask &= (all_dessert_shops_df["rating"] >= search_query_parameters[0]) & (
                all_dessert_shops_df["rating"] <= search_query_parameters[1]
            )

        elif col == "budget":
            mask &= all_dessert_shops_df["price_per_person"] <= search_query_parameters

        elif col == "price_level":
            if "price_level" in all_dessert_shops_df.columns:
                mask &= all_dessert_shops_df["price_level"].isin(search_query_parameters)

        elif col.startswith("has_"):
            if col in all_dessert_shops_df.columns:
                mask &= all_dessert_shops_df[col] == search_query_parameters

    resulting_shops = (all_dessert_shops_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)

    if len(resulting_shops) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_shops,
            query_summary=f"{summarized_query}\nThere are 0 dessert shop(s) that matched this query!",
        )
    final_results = resulting_shops[:10]
    return SearchResultsOutputModel(
        search_results=final_results,
        query_summary=f"{summarized_query}\nThere are {len(final_results)} dessert shop(s) that matched this query!",
    )
