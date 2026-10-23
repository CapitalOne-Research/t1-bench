import pandas as pd
from pathlib import Path
from typing import Any

from t1_plus_plus.schema.kayak.get_kayak_rental_details import GetRentalDetailsInputModel, GetRentalDetailsOutputModel
from t1_plus_plus.schema.kayak.kayak_rental_item import KayakRentalItem

# Load the CSV — resolve relative to this file so it works regardless of cwd or import path
_data_dir = Path(__file__).resolve().parents[4] / "datasets"
_CSV_PATH = str(_data_dir / "data_kayak_rental.csv")
try:
    all_kayak_df = pd.read_csv(_CSV_PATH)
except FileNotFoundError:
    all_kayak_df = pd.DataFrame()


def get_rental_details(**kwargs: Any) -> GetRentalDetailsOutputModel:
    """
    Retrieve full details for a specific rental location based on rental_id.
    """
    try:
        input_data = GetRentalDetailsInputModel.model_validate(kwargs)
    except Exception as e:
        return GetRentalDetailsOutputModel(status="error", message=str(e), rental_details=None)

    if all_kayak_df.empty:
        return GetRentalDetailsOutputModel(
            status="error", message="Database is currently unavailable.", rental_details=None
        )

    # Filter for specific rental_id
    rental_row = all_kayak_df[all_kayak_df["rental_id"] == input_data.rental_id]

    if rental_row.empty:
        return GetRentalDetailsOutputModel(
            status="error",
            message=f"No rental business found with ID: {input_data.rental_id}",
            rental_details=None
        )

    # Convert the single row to a dictionary and then to a KayakRentalItem
    rental_dict = rental_row.iloc[0].to_dict()
    rental_item = KayakRentalItem(**rental_dict)

    return GetRentalDetailsOutputModel(
        status="success",
        message="Rental details successfully retrieved.",
        rental_details=rental_item
    )
