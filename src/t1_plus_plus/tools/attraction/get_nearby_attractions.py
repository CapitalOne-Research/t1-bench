from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any

import pandas as pd

from t1_plus_plus.schema.attraction.attraction import (
    Attraction,
    GetNearbyAttractionsInputModel,
    GetNearbyAttractionsOutputModel,
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


def _haversine_miles(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    earth_radius_miles = 3958.7613

    lat1 = radians(latitude_1)
    lon1 = radians(longitude_1)
    lat2 = radians(latitude_2)
    lon2 = radians(longitude_2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return earth_radius_miles * c


def get_nearby_attractions(**kwargs: Any) -> GetNearbyAttractionsOutputModel:
    """
    Description:
        Use this tool to find attractions near a given location, specified by coordinates or an attraction name.

    Examples:
    >>> # Usage Example:
    get_nearby_attractions(attraction_name="Central Park", radius_miles=5.0)

    >>> # Usage Example:
    get_nearby_attractions(latitude=40.7829, longitude=-73.9654, radius_miles=10.0, attraction_type="Museum")

    Returns:
        GetNearbyAttractionsOutputModel: Output containing the nearby attractions.
    """
    request = GetNearbyAttractionsInputModel.model_validate(kwargs)

    df = _load_attractions()

    # Resolve coordinates from attraction name if lat/lon not provided
    ref_lat = request.latitude
    ref_lon = request.longitude
    if ref_lat is None or ref_lon is None:
        if not request.attraction_name:
            return GetNearbyAttractionsOutputModel(
                status="error",
                message="Either latitude/longitude or attraction_name must be provided.",
                attractions=[],
            )
        anchor_df = df[df["name"].str.lower() == request.attraction_name.strip().lower()]
        if request.attraction_city:
            anchor_df = anchor_df[anchor_df["city"].str.lower() == request.attraction_city.strip().lower()]
        if anchor_df.empty:
            return GetNearbyAttractionsOutputModel(
                status="error",
                message=f"Attraction '{request.attraction_name}' not found.",
                attractions=[],
            )
        ref_lat = float(anchor_df.iloc[0]["latitude"])
        ref_lon = float(anchor_df.iloc[0]["longitude"])

    if request.attraction_type:
        df = df[df["type"].str.lower() == request.attraction_type.strip().lower()]

    if request.min_rating is not None:
        df = df[df["rating"] >= request.min_rating]

    working_df = df.copy()
    working_df["distance_miles"] = working_df.apply(
        lambda row: _haversine_miles(
            ref_lat,
            ref_lon,
            float(row["latitude"]),
            float(row["longitude"]),
        ),
        axis=1,
    )

    working_df = working_df[working_df["distance_miles"] <= request.radius_miles]
    working_df["distance_miles"] = working_df["distance_miles"].round(2)

    working_df = working_df.sort_values(
        by=["distance_miles", "rating", "name"],
        ascending=[True, False, True],
    ).head(10)

    attractions = [Attraction(**record) for record in working_df.to_dict(orient="records")]

    return GetNearbyAttractionsOutputModel(
        status="success",
        message=f"Found {len(attractions)} nearby attraction(s).",
        attractions=attractions,
    )
