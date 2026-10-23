from pathlib import Path
from typing import Any

import pandas as pd

from t1_plus_plus.schema.attraction.attraction import (
    Attraction,
    GetTopAttractionsInputModel,
    GetTopAttractionsOutputModel,
)


DATASET_PATH = Path(__file__).resolve().parents[4] / "datasets" / "data_attractions.csv"


def _load_attractions() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH)

    unnamed_columns = [column for column in df.columns if str(column).startswith("Unnamed:")]
    if unnamed_columns:
        df = df.drop(columns=unnamed_columns)

    for column in ["city", "state", "name", "type"]:
        df[column] = df[column].astype(str).str.strip()

    for column in ["latitude", "longitude", "rating"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["city", "state", "name", "type", "latitude", "longitude", "rating"])
    return df.reset_index(drop=True)


def get_top_attractions(**kwargs: Any) -> GetTopAttractionsOutputModel:
    """
    Description:
        Use this tool to retrieve the top-rated attractions in a given city.

    Examples:
    >>> # Usage Example:
    get_top_attractions(city="New York", state="NY", attraction_type="Museum")

    >>> # Usage Example:
    get_top_attractions(city="Chicago")

    Returns:
        GetTopAttractionsOutputModel: Output containing the top attractions.
    """
    request = GetTopAttractionsInputModel.model_validate(kwargs)

    df = _load_attractions()
    df = df[df["city"].str.lower() == request.city.strip().lower()]

    if request.state:
        df = df[df["state"].str.lower() == request.state.strip().lower()]

    if request.attraction_type:
        df = df[df["type"].str.lower() == request.attraction_type.strip().lower()]

    df = df.sort_values(
        by=["rating", "name"],
        ascending=[False, True],
    ).head(10)

    attractions = [Attraction(**record) for record in df.to_dict(orient="records")]

    return GetTopAttractionsOutputModel(
        status="success",
        message=f"Found {len(attractions)} top attraction(s) for the requested city.",
        attractions=attractions,
    )
