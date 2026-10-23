import os

import numpy as np
import pandas as pd
from pathlib import Path

from t1_plus_plus.schema.food_and_dining.search_food_and_dining import SearchFoodAndDiningInputModel
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
CSV_PATH = os.getenv("ALL_FOOD_AND_DINING", str(_data_dir / "data_food_and_dining.csv"))
try:
    all_food_and_dining_df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    all_food_and_dining_df = pd.DataFrame()


def summarize_query(params: dict) -> str:
    result = []

    if "city" in params:
        city_str = params["city"]
        if "state" in params:
            city_str += f", {params['state']}"
        result.append(f"Food and dining search results in {city_str},")
    if "neighborhood" in params:
        result.append(f"in neighborhood(s) [{', '.join(params['neighborhood'])}],")
    if "cuisine" in params:
        result.append(f"serving [{', '.join(params['cuisine'])}],")
    if "restaurant_name" in params:
        result.append(f"for establishment(s) [{', '.join(params['restaurant_name'])}],")
    if "restaurant_id" in params:
        result.append(f"with ID(s) [{', '.join(params['restaurant_id'])}],")
    if "price_per_person" in params:
        result.append(f"budget <= ${params['price_per_person']},")
    if "rating" in params:
        r = params["rating"]
        result.append(f"rating between {r[0]} and {r[1]},")

    bool_features = [
        k for k, v in params.items()
        if (k.startswith("has_") or k.startswith("is_") or k.startswith("supports_"))
        and v is True
    ]
    if bool_features:
        names = ", ".join(
            f.replace("has_", "").replace("is_", "").replace("supports_", "supports ").replace("_", " ")
            for f in bool_features
        )
        result.append(f"with features: [{names}],")

    summary = " ".join(result)
    if summary.endswith(","):
        summary = summary[:-1] + "."
    return summary


def search_food_and_dining(**kwargs) -> SearchResultsOutputModel:
    """
    Description:
        Search for food and dining establishments by city and state, cuisine, features, dietary needs,
        service options, and more. 'city' and 'state' MUST be provided.

    Examples:
    >>> # Usage Example: Search by city, state and cuisine
    search_food_and_dining(city="Austin", state="TX", cuisine="Tapas")

    >>> # Usage Example: Search with dietary and service filters
    search_food_and_dining(city="Chicago", state="IL", has_curbside_pickup=True, vegan_options=True)

    >>> # Usage Example: Search with budget and open-now filter
    search_food_and_dining(city="Denver", state="CO", cuisine="Burger", is_open=True, price_per_person=30.0)

    Returns:
        SearchResultsOutputModel: Matching establishments and a query summary.
    """
    try:
        search_input = SearchFoodAndDiningInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"Input validation error: {str(e)}"
        )

    params = {k: v for k, v in search_input.model_dump(exclude_none=True).items()}

    if all_food_and_dining_df.empty:
        return SearchResultsOutputModel(
            search_results=[], query_summary="Database is currently unavailable."
        )

    mask = pd.Series(True, index=all_food_and_dining_df.index)

    for col, val in params.items():
        if col == "city":
            mask &= all_food_and_dining_df["city"] == val

        elif col == "state":
            mask &= all_food_and_dining_df["state"] == val

        elif col == "neighborhood":
            mask &= all_food_and_dining_df["neighborhood"].isin(val)

        elif col == "cuisine":
            cuisine_masks = [
                all_food_and_dining_df["cuisine"].str.lower().str.contains(c.lower(), na=False)
                for c in val
            ]
            mask &= np.logical_or.reduce(cuisine_masks)

        elif col == "restaurant_name":
            mask &= all_food_and_dining_df["name"].isin(val)

        elif col == "restaurant_id":
            mask &= all_food_and_dining_df["id"].isin(val)

        elif col == "price_per_person":
            mask &= all_food_and_dining_df["price_per_person"] <= val

        elif col == "price_level":
            if "price_level" in all_food_and_dining_df.columns:
                mask &= all_food_and_dining_df["price_level"].isin(val)

        elif col == "rating":
            mask &= (all_food_and_dining_df["rating"] >= val[0]) & (
                all_food_and_dining_df["rating"] <= val[1]
            )

        elif col in all_food_and_dining_df.columns:
            mask &= all_food_and_dining_df[col] == val

    results = all_food_and_dining_df[mask].to_dict(orient="records")
    summary = summarize_query(params)

    if not results:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{summary}\nThere are 0 establishment(s) that matched this query!",
        )

    extracted = [
        {
            "restaurant_id": item.get("id"),
            "name": item.get("name"),
            "city": item.get("city"),
            "state": item.get("state"),
            "neighborhood": item.get("neighborhood"),
            "cuisine": item.get("cuisine"),
            "price_per_person": item.get("price_per_person"),
            "price_level": item.get("price_level"),
            "rating": item.get("rating"),
            "supports_delivery": item.get("supports_delivery"),
            "is_open": item.get("is_open"),
        }
        for item in results[:10]
    ]

    return SearchResultsOutputModel(
        search_results=extracted,
        query_summary=f"{summary}\nThere are {len(extracted)} establishment(s) that matched this query!",
    )
