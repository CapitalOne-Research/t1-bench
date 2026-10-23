from pathlib import Path
from typing import Any

import pandas as pd

from t1_plus_plus.schema.attraction.attraction import (
    Attraction,
    SearchAttractionsInputModel,
)
from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel

DATASET_PATH = Path(__file__).resolve().parents[4] / "datasets" / "data_attractions.csv"


def _load_attractions() -> pd.DataFrame:
    try:
        df = pd.read_csv(DATASET_PATH)
    except FileNotFoundError:
        return pd.DataFrame()

    unnamed_columns = [
        column for column in df.columns if str(column).startswith("Unnamed:")
    ]
    if unnamed_columns:
        df = df.drop(columns=unnamed_columns)

    for column in ["city", "state", "name", "type"]:
        df[column] = df[column].astype(str).str.strip()

    for column in ["latitude", "longitude", "rating"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(
        subset=["city", "state", "name", "type", "latitude", "longitude", "rating"]
    )
    return df.reset_index(drop=True)


def search_attractions(
    **kwargs: SearchAttractionsInputModel,
) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for attractions based on several criteria such as city, state, attraction type, and minimum rating.

    Examples:
    >>> # Usage Example:
    search_attractions(city="New York", attraction_type="Museum", min_rating=4.5)

    >>> # Usage Example:
    search_attractions(state="CA", attraction_type="Park")

    >>> # Usage Example:
    search_attractions(city="Chicago", min_rating=4.0)

    Returns:
        SearchResultsOutputModel: Output containing the search results and query summary.
    """
    try:
        request = SearchAttractionsInputModel.model_validate(kwargs)
    except Exception as e:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"Input validation error: {str(e)}",
        )

    df = _load_attractions()

    if df.empty:
        return SearchResultsOutputModel(
            search_results=[],
            query_summary="Database is currently unavailable.",
        )

    request_filtered = {
        key: value for key, value in request.model_dump().items() if value is not None
    }

    mask = pd.Series(True, index=df.index)

    for col, value in request_filtered.items():
        if col == "city":
            mask &= df["city"].str.lower() == value.lower()

        elif col == "state":
            mask &= df["state"].str.lower() == value.lower()

        elif col == "attraction_type":
            mask &= df["type"].str.lower() == value.lower()

        elif col == "min_rating":
            mask &= df["rating"] >= value

    filtered_df = df[mask]

    filtered_df = filtered_df.sort_values(
        by=["rating", "city", "name"],
        ascending=[False, True, True],
    ).head(10)

    allowed_fields = set(Attraction.model_fields.keys())
    attractions = [
        Attraction.model_validate(
            {key: value for key, value in record.items() if key in allowed_fields}
        ).model_dump()
        for record in filtered_df.to_dict(orient="records")
    ]

    return SearchResultsOutputModel(
        search_results=attractions,
        query_summary=f"Found {len(attractions)} attraction(s).",
    )
