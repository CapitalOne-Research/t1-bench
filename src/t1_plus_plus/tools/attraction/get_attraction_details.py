from pathlib import Path
from typing import Any

import pandas as pd

from t1_plus_plus.schema.attraction.attraction import (
    Attraction,
    GetAttractionDetailsInputModel,
    GetAttractionDetailsOutputModel,
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


def get_attraction_details(**kwargs: Any) -> GetAttractionDetailsOutputModel:
    """
    Description:
        Use this tool to retrieve detailed information about a specific attraction by name.

    Examples:
    >>> # Usage Example:
    get_attraction_details(name="Central Park", city="New York", state="NY")

    >>> # Usage Example:
    get_attraction_details(name="Golden Gate Park")

    Returns:
        GetAttractionDetailsOutputModel: Output containing the attraction details.
    """
    request = GetAttractionDetailsInputModel.model_validate(kwargs)

    df = _load_attractions()

    if request.city:
        df = df[df["city"].str.lower() == request.city.strip().lower()]

    if request.state:
        df = df[df["state"].str.lower() == request.state.strip().lower()]

    exact_matches = df[df["name"].str.lower() == request.name.strip().lower()]
    if not exact_matches.empty:
        exact_matches = exact_matches.sort_values(
            by=["rating", "city", "name"],
            ascending=[False, True, True],
        )
        attraction = Attraction(**exact_matches.iloc[0].to_dict())
        return GetAttractionDetailsOutputModel(
            status="success",
            message="Attraction found.",
            attraction=attraction,
        )

    partial_matches = df[df["name"].str.lower().str.contains(request.name.strip().lower(), na=False)]
    if not partial_matches.empty:
        partial_matches = partial_matches.sort_values(
            by=["rating", "city", "name"],
            ascending=[False, True, True],
        )
        attraction = Attraction(**partial_matches.iloc[0].to_dict())
        return GetAttractionDetailsOutputModel(
            status="success",
            message="Closest matching attraction found.",
            attraction=attraction,
        )

    return GetAttractionDetailsOutputModel(
        status="error",
        message="No attraction matched the requested name.",
    )
