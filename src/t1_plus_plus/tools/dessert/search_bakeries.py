import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.dessert.search_bakeries import SearchBakeriesInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

data_dir = Path(__file__).resolve().parents[4] / "datasets"

CSV_PATH = str(data_dir / "data_bakery.csv")
try:
    all_bakeries_df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    all_bakeries_df = pd.DataFrame()


def summarize_query(search_input_filtered):
    result = []

    if "city" in search_input_filtered:
        result.append("Bakery search results in {},".format(search_input_filtered["city"]))

    if "neighborhood" in search_input_filtered:
        neighborhoods = ", ".join(search_input_filtered["neighborhood"])
        result.append("in neighborhood(s) [{}],".format(neighborhoods))

    if "bakery_name" in search_input_filtered:
        names = ", ".join(search_input_filtered["bakery_name"])
        result.append("for bakery(s) [{}],".format(names))

    if "bakery_id" in search_input_filtered:
        ids = ", ".join(search_input_filtered["bakery_id"])
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
            [f.replace("has_has_", "").replace("has_", "").replace("_", " ") for f in features]
        )
        result.append("with features: [{}],".format(feature_names))

    final_result = " ".join(result)
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."

    return final_result


def search_bakeries(**kwargs: SearchBakeriesInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for bakeries based on criteria such as city,
        neighborhood, rating, price level, bread specialties, service options,
        and dietary options. Note - 'city' MUST be provided.

    Examples:
    >>> # Usage Example:
    search_bakeries(city="New York", has_sourdough=True, has_wedding_cakes=True)

    >>> # Usage Example:
    search_bakeries(city="New York", rating=[4.0, 5.0], has_has_gluten_free_options=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting bakeries as well as the summary.
    """
    try:
        search_input = SearchBakeriesInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    search_input_filtered = {
        k: v for k, v in search_input.model_dump().items() if v is not None
    }

    if all_bakeries_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    mask = pd.Series(True, index=all_bakeries_df.index)

    for col, search_query_parameters in search_input_filtered.items():
        if col == "city":
            mask &= all_bakeries_df["city"] == search_query_parameters

        elif col == "neighborhood":
            mask &= all_bakeries_df["neighborhood"].isin(search_query_parameters)

        elif col == "bakery_name":
            mask &= all_bakeries_df["name"].isin(search_query_parameters)

        elif col == "bakery_id":
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
                mask &= all_bakeries_df[col] == search_query_parameters

    resulting_bakeries = (all_bakeries_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)

    if len(resulting_bakeries) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_bakeries,
            query_summary=f"{summarized_query}\nThere are 0 bakery(s) that matched this query!",
        )
    final_results = resulting_bakeries[:10]
    return SearchResultsOutputModel(
        search_results=final_results,
        query_summary=f"{summarized_query}\nThere are {len(final_results)} bakery(s) that matched this query!",
    )
