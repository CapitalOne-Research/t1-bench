import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.cafe.search_cafes import SearchCafesInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

data_dir = Path(__file__).resolve().parents[4] / "datasets"

COFFEE_CSV = str(data_dir / "data_coffee_shop.csv")
BOBA_CSV = str(data_dir / "data_bubble_tea.csv")

try:
    coffee_df = pd.read_csv(COFFEE_CSV)
    coffee_df["cafe_type"] = "Coffee Shop"
except FileNotFoundError:
    coffee_df = pd.DataFrame()

try:
    boba_df = pd.read_csv(BOBA_CSV)
    boba_df["cafe_type"] = "Bubble Tea"
except FileNotFoundError:
    boba_df = pd.DataFrame()

all_cafes_df = pd.concat([coffee_df, boba_df], ignore_index=True)


def summarize_query(search_input_filtered):
    result = []

    if "city" in search_input_filtered:
        result.append("Cafe search results in {},".format(search_input_filtered["city"]))

    if "cafe_type" in search_input_filtered:
        result.append("type [{}],".format(search_input_filtered["cafe_type"]))

    if "neighborhood" in search_input_filtered:
        neighborhoods = ", ".join(search_input_filtered["neighborhood"])
        result.append("in neighborhood(s) [{}],".format(neighborhoods))

    if "cafe_name" in search_input_filtered:
        names = ", ".join(search_input_filtered["cafe_name"])
        result.append("for cafe(s) [{}],".format(names))

    if "cafe_id" in search_input_filtered:
        ids = ", ".join(search_input_filtered["cafe_id"])
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
        if k.startswith("has_") and v is True
    ]
    if features:
        feature_names = ", ".join(
            [f.replace("has_", "").replace("_", " ") for f in features]
        )
        result.append("with features: [{}],".format(feature_names))

    final_result = " ".join(result)
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."

    return final_result


def search_cafes(**kwargs: SearchCafesInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for cafes (coffee shops and/or bubble tea shops) based on
        criteria such as city, cafe type, neighborhood, budget, ratings, and various features
        (like milk alternatives, roast types, tea bases, toppings, etc.).
        Note - 'city' MUST be provided.

    Examples:
    >>> # Usage Example:
    search_cafes(city="New York", cafe_type="Coffee Shop", has_oat=True, has_dark_roast=True)

    >>> # Usage Example:
    search_cafes(city="New York", cafe_type="Bubble Tea", has_matcha=True, has_brown_sugar_pearls=True)

    >>> # Usage Example:
    search_cafes(city="New York", rating=[4.0, 5.0], has_almond=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting cafes as well as the summary.
    """
    try:
        search_input = SearchCafesInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    search_input_filtered = {
        k: v for k, v in search_input.model_dump().items() if v is not None
    }

    if all_cafes_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    mask = pd.Series(True, index=all_cafes_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "city":
            mask &= all_cafes_df["city"] == search_query_parameters

        elif col == "cafe_type":
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
                mask &= all_cafes_df[col] == search_query_parameters

    resulting_cafes = (all_cafes_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)

    if len(resulting_cafes) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_cafes,
            query_summary=f"{summarized_query}",
        )
    final_results = resulting_cafes[:10]
    result = SearchResultsOutputModel(
        search_results=final_results,
        query_summary=f"{summarized_query}\nThere are {len(final_results)} cafe(s) that matched this query!",
    )

    return result
